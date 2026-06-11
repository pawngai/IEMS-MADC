import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Permissions } from "@/platform/permissions";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { getEmployeeCompletionStatus } from "@/shared/lib/utils";
import { filterQueuedProfilesByStage, getProfileQueueStagesForAuthority } from "@/shared/lib/profileWorkflowQueue";
import { toast } from "sonner";
import {
  getMyEssProfile,
  clearWorkQueueInflightRequests,
  listIdentitiesByStatus,
  listChangeRequestsByStatus,
  listProfilesByStatus,
  listServiceBookQueue,
  listServiceBookOpeningQueue,
} from "@/contexts/workflow/model/workQueueGateway";
import {
  enrichAndSortQueueItems,
  toChangeRequestItems,
  toEssTaskItem,
  toIdentityItems,
  toProfileItems,
  toServiceBookItems,
  toServiceBookOpeningItems,
} from "@/contexts/workflow/model/workflowQueueMapper";

const normalizeStage = (value) => String(value || "").trim().toUpperCase();

export function useWorkflowQueueQuery() {
  const { user } = useAuth();
  const {
    can,
    canAny,
    canAccessModule,
    canAccessEssPortal,
    getPrimaryAuthority,
    getAuthorityDisplayName,
  } = usePermissions();

  const authority = getPrimaryAuthority();
  const authorityLabel = getAuthorityDisplayName(authority);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [items, setItems] = useState([]);
  const mountedRef = useRef(true);
  const loadRequestIdRef = useRef(0);

  const canServiceBookWorkflow =
    canAny([
      Permissions.SERVICE_BOOK_ENTRY_CREATE,
      Permissions.SERVICE_BOOK_ENTRY_SUBMIT,
      Permissions.SERVICE_BOOK_ENTRY_VERIFY,
      Permissions.SERVICE_BOOK_ENTRY_APPROVE,
      Permissions.SERVICE_BOOK_ENTRY_ATTEST,
    ]) && can(Permissions.SERVICE_BOOK_READ_ALL);

  const canServiceBookOpeningWorkflow =
    canAny([
      Permissions.SERVICE_BOOK_OPENING_CREATE,
      Permissions.SERVICE_BOOK_OPENING_UPDATE,
      Permissions.SERVICE_BOOK_OPENING_SUBMIT,
      Permissions.SERVICE_BOOK_OPENING_VERIFY,
      Permissions.SERVICE_BOOK_OPENING_APPROVE,
    ]) && can(Permissions.SERVICE_BOOK_READ_ALL);

  const canChangeRequestReview =
    can(Permissions.PROFILE_READ_ALL) && can(Permissions.PROFILE_UPDATE_ALL);

  const canIdentityWorkflow = useMemo(() => {
    if (["SYSTEM_ADMIN", "EMPLOYEE"].includes(authority)) return false;
    if (["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"].includes(authority)) {
      return canAccessModule("data_entry");
    }
    if (authority === "VERIFIER") return canAccessModule("verification");
    if (authority === "APPROVING_AUTHORITY") return canAccessModule("approval");
    return false;
  }, [authority, canAccessModule]);

  const canProfileWorkflow = useMemo(() => {
    if (authority === "SYSTEM_ADMIN") return false;
    if (authority === "EMPLOYEE") return canAccessEssPortal();
    if (["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SECTION_OFFICER"].includes(authority)) {
      return canAccessModule("data_entry");
    }
    if (authority === "VERIFIER") return canAccessModule("verification");
    if (["APPROVING_AUTHORITY", "DDO"].includes(authority)) return canAccessModule("approval");
    if (["HOD", "APPOINTING_AUTHORITY", "DISCIPLINARY_AUTHORITY"].includes(authority)) {
      return canAccessModule("attestation");
    }
    return true;
  }, [authority, canAccessModule, canAccessEssPortal]);

  const shouldLoadProfileQueueItems = useMemo(() => {
    if (!canProfileWorkflow) return false;
    return true;
  }, [authority, canProfileWorkflow]);

  const profileStages = useMemo(() => getProfileQueueStagesForAuthority(authority), [authority]);

  const load = useCallback(
    async (mode = "initial") => {
      const requestId = loadRequestIdRef.current + 1;
      loadRequestIdRef.current = requestId;
      const isCurrentRequest = () => mountedRef.current && loadRequestIdRef.current === requestId;

      if (mode === "initial") setLoading(true);
      else setRefreshing(true);

      try {
        clearWorkQueueInflightRequests();
        const queueTasks = [];

        if (authority === "EMPLOYEE" && canAccessEssPortal()) {
          queueTasks.push(async () => {
            const profile = await getMyEssProfile();
            const completion = getEmployeeCompletionStatus(profile);
            const ready = completion.known ? completion.complete : false;
            const status = profile?.workflow_status || "DRAFT";
            if (!ready && ["DRAFT", "REJECTED"].includes(status)) {
              return [toEssTaskItem({ profile, user })];
            }
            return [];
          });
        }

        if (
          shouldLoadProfileQueueItems &&
          canAny([
            Permissions.PROFILE_READ_ALL,
            Permissions.PROFILE_CREATE,
            Permissions.PROFILE_UPDATE_ALL,
            Permissions.PROFILE_UPDATE_OWN_LIMITED,
          ])
        ) {
          queueTasks.push(async () => {
            const stageItems = await Promise.all(profileStages.map(async (stage) => {
              const profiles = await listProfilesByStatus(stage, 200);
              return toProfileItems({ profiles: filterQueuedProfilesByStage(profiles, stage), stage });
            }));
            return stageItems.flat();
          });
        }

        if (canIdentityWorkflow) {
          queueTasks.push(async () => {
            const tasks = [];

            if (["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"].includes(authority)) {
              tasks.push(listIdentitiesByStatus("DRAFT", 200).then((identities) => toIdentityItems({ identities, stage: "DRAFT" })));
              tasks.push(listIdentitiesByStatus("REJECTED", 200).then((identities) => toIdentityItems({ identities, stage: "REJECTED" })));
            } else if (authority === "VERIFIER") {
              tasks.push(listIdentitiesByStatus("SUBMITTED", 200).then((identities) => toIdentityItems({ identities, stage: "SUBMITTED" })));
            } else if (authority === "APPROVING_AUTHORITY") {
              tasks.push(listIdentitiesByStatus("VERIFIED", 200).then((identities) => toIdentityItems({ identities, stage: "VERIFIED" })));
            }

            const stageItems = await Promise.all(tasks);
            return stageItems.flat();
          });
        }

        if (canServiceBookWorkflow) {
          const serviceBookStages = [];
          if (can(Permissions.SERVICE_BOOK_ENTRY_CREATE) || can(Permissions.SERVICE_BOOK_ENTRY_SUBMIT)) {
            serviceBookStages.push("DRAFT", "REJECTED");
          }
          if (can(Permissions.SERVICE_BOOK_ENTRY_VERIFY)) {
            serviceBookStages.push("SUBMITTED");
          }
          if (can(Permissions.SERVICE_BOOK_ENTRY_APPROVE)) {
            serviceBookStages.push("VERIFIED");
          }
          if (can(Permissions.SERVICE_BOOK_ENTRY_ATTEST)) {
            serviceBookStages.push("APPROVED");
          }

          if (serviceBookStages.length > 0) {
            queueTasks.push(async () => {
              const stageSet = new Set(serviceBookStages);
              const workflowState = serviceBookStages.length === 1 ? serviceBookStages[0] : serviceBookStages;
              const entries = await listServiceBookQueue(workflowState, 200);
              return serviceBookStages.flatMap((stage) => toServiceBookItems({
                entries: entries.filter((entry) => {
                  const entryStage = normalizeStage(entry.workflow_state || entry.status);
                  return stageSet.has(entryStage) && entryStage === stage;
                }),
                stage,
              }));
            });
          }
        }

        if (canServiceBookOpeningWorkflow) {
          const openingStages = [];
          if (can(Permissions.SERVICE_BOOK_OPENING_CREATE) || can(Permissions.SERVICE_BOOK_OPENING_UPDATE) || can(Permissions.SERVICE_BOOK_OPENING_SUBMIT)) {
            openingStages.push("DRAFT", "REJECTED");
          }
          if (can(Permissions.SERVICE_BOOK_OPENING_VERIFY)) {
            openingStages.push("SUBMITTED");
          }
          if (can(Permissions.SERVICE_BOOK_OPENING_APPROVE)) {
            openingStages.push("VERIFIED");
          }

          if (openingStages.length > 0) {
            queueTasks.push(async () => {
              const stageItems = await Promise.all(openingStages.map(async (stage) => {
                const openings = await listServiceBookOpeningQueue(stage, 200);
                return toServiceBookOpeningItems({ openings, stage });
              }));
              return stageItems.flat();
            });
          }
        }

        if (canChangeRequestReview) {
          queueTasks.push(async () => {
            const items = await listChangeRequestsByStatus("PENDING");
            return toChangeRequestItems({ items, stage: "SUBMITTED" });
          });
        }

        const queueItemGroups = await Promise.all(queueTasks.map((task) => task()));
        const nextItems = queueItemGroups.flat().filter(Boolean);

        if (isCurrentRequest()) {
          setItems(enrichAndSortQueueItems(nextItems));
        }
      } catch (error) {
        if (isCurrentRequest()) {
          console.error("Work queue load failed:", error);
          toast.error("Failed to load work queue");
          setItems([]);
        }
      } finally {
        if (isCurrentRequest()) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [authority, can, canAny, canAccessEssPortal, canServiceBookOpeningWorkflow, canServiceBookWorkflow, canChangeRequestReview, canIdentityWorkflow, profileStages, shouldLoadProfileQueueItems, user]
  );

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    load("initial");
  }, [load]);

  const refresh = useCallback(() => load("refresh"), [load]);

  return {
    loading,
    refreshing,
    items,
    refresh,
    authority,
    authorityLabel,
  };
}

export default useWorkflowQueueQuery;
