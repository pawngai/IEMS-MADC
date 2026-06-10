import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Layout from "@/app/layout/Layout";
import { analyticsAPI } from "@/contexts/analytics/api/analyticsApi";
import { mastersAPI } from "@/contexts/masters";
import { useAuth } from "@/contexts/identity";
import { Permissions } from "@/platform/permissions";
import { Button } from "@/shared/ui/button";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton } from "@/shared/ui/skeletons";
import {
  BarChart3,
  Calendar,
  ClipboardList,
  GitBranch,
  Loader2,
  RefreshCw,
  Users,
} from "lucide-react";
import { toast } from "sonner";
import {
  AnalyticsDataNotice,
  AnalyticsDrilldownSheet,
  AnalyticsInteractionHint,
  AnalyticsSectionLoader,
  ANALYTICS_SECTION_CONFIG,
  LeavePanel,
  OverviewPanel,
  ServiceEventsPanel,
  WorkforcePanel,
  WorkflowPanel,
} from "@/contexts/analytics/components/AnalyticsDashboardSections";
import {
  DRILLDOWN_ROW_LIMIT,
  buildAnalyticsDrilldownKey,
  buildLeaveTypeNameMap,
  buildMasterNameMap,
  buildServiceEventTypeNameMap,
  formatLeaveAnalytics,
  formatServiceEventsAnalytics,
  formatWorkforceAnalytics,
} from "@/contexts/analytics/model/analyticsDashboardModel";

const TAB_SECTION_KEYS = {
  overview: ["overview", "workflow"],
  workforce: ["workforce"],
  leave: ["leave"],
  workflow: ["workflow"],
  events: ["serviceEvents"],
};

/* ─── main component ────────────────────────────────────────────── */

const AnalyticsDashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [overview, setOverview] = useState(null);
  const [workforce, setWorkforce] = useState(null);
  const [leave, setLeave] = useState(null);
  const [workflow, setWorkflow] = useState(null);
  const [serviceEvents, setServiceEvents] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [failedSectionKeys, setFailedSectionKeys] = useState([]);
  const [sectionLoading, setSectionLoading] = useState({
    overview: false,
    workforce: false,
    leave: false,
    workflow: false,
    serviceEvents: false,
  });
  const [drilldownState, setDrilldownState] = useState({
    open: false,
    loading: false,
    config: null,
    data: null,
    error: null,
  });
  const loadedSectionsRef = useRef(new Set());
  const mountedRef = useRef(true);
  const sectionRequestIdsRef = useRef({});
  const initialLoadRequestIdRef = useRef(0);
  const refreshRequestIdRef = useRef(0);
  const drilldownRequestIdRef = useRef(0);
  const departmentNameMapRef = useRef(null);
  const designationNameMapRef = useRef(null);
  const officeNameMapRef = useRef(null);
  const serviceNameMapRef = useRef(null);
  const serviceGroupNameMapRef = useRef(null);
  const serviceEventTypeNameMapRef = useRef(null);
  const leaveTypeNameMapRef = useRef(null);
  const { can } = useAuth();
  const canOpenEmployees = can(Permissions.PROFILE_READ_ALL);
  const canOpenServiceEvents = can(Permissions.SERVICE_BOOK_READ_ALL);

  const failedSections = useMemo(
    () => failedSectionKeys.map((key) => ANALYTICS_SECTION_CONFIG[key]?.label || key),
    [failedSectionKeys],
  );

  const getWorkforceNameMaps = useCallback(async () => {
    if (
      departmentNameMapRef.current
      && designationNameMapRef.current
      && officeNameMapRef.current
      && serviceNameMapRef.current
      && serviceGroupNameMapRef.current
    ) {
      return {
        departmentNameMap: departmentNameMapRef.current,
        designationNameMap: designationNameMapRef.current,
        officeNameMap: officeNameMapRef.current,
        serviceNameMap: serviceNameMapRef.current,
        serviceGroupNameMap: serviceGroupNameMapRef.current,
      };
    }

    const [departmentsResponse, designationsResponse, officesResponse, servicesResponse, serviceGroupsResponse] = await Promise.all([
      mastersAPI.getDepartments().catch(() => ({ data: [] })),
      mastersAPI.getDesignations().catch(() => ({ data: [] })),
      mastersAPI.getOffices().catch(() => ({ data: [] })),
      mastersAPI.getServices().catch(() => ({ data: [] })),
      mastersAPI.getServiceGroups().catch(() => ({ data: [] })),
    ]);

    departmentNameMapRef.current = buildMasterNameMap(departmentsResponse.data);
    designationNameMapRef.current = buildMasterNameMap(designationsResponse.data);
    officeNameMapRef.current = buildMasterNameMap(officesResponse.data);
    serviceNameMapRef.current = buildMasterNameMap(servicesResponse.data);
    serviceGroupNameMapRef.current = buildMasterNameMap(serviceGroupsResponse.data);

    return {
      departmentNameMap: departmentNameMapRef.current,
      designationNameMap: designationNameMapRef.current,
      officeNameMap: officeNameMapRef.current,
      serviceNameMap: serviceNameMapRef.current,
      serviceGroupNameMap: serviceGroupNameMapRef.current,
    };
  }, []);

  const getServiceEventTypeNameMap = useCallback(async () => {
    if (serviceEventTypeNameMapRef.current) return serviceEventTypeNameMapRef.current;

    const serviceEventTypesResponse = await mastersAPI.getServiceEventTypes().catch(() => ({ data: [] }));
    serviceEventTypeNameMapRef.current = buildServiceEventTypeNameMap(serviceEventTypesResponse.data);
    return serviceEventTypeNameMapRef.current;
  }, []);

  const getLeaveTypeNameMap = useCallback(async () => {
    if (leaveTypeNameMapRef.current) return leaveTypeNameMapRef.current;

    const leaveTypesResponse = await mastersAPI.getLeaveTypes().catch(() => ({ data: [] }));
    leaveTypeNameMapRef.current = buildLeaveTypeNameMap(leaveTypesResponse.data);
    return leaveTypeNameMapRef.current;
  }, []);

  const ensureDrilldownMaps = useCallback(async (section) => {
    if (section === "workforce") {
      await getWorkforceNameMaps();
      return;
    }
    if (section === "leave") {
      await getLeaveTypeNameMap();
      return;
    }
    if (section === "serviceEvents") {
      await getServiceEventTypeNameMap();
    }
  }, [getLeaveTypeNameMap, getServiceEventTypeNameMap, getWorkforceNameMaps]);

  const applySectionData = useCallback(async (key, data) => {
    if (key === "overview") {
      setOverview(data);
      return;
    }

    if (key === "workflow") {
      setWorkflow(data);
      return;
    }

    if (key === "workforce") {
      const { departmentNameMap, designationNameMap } = await getWorkforceNameMaps();
      setWorkforce(formatWorkforceAnalytics(data, departmentNameMap, designationNameMap));
      return;
    }

    if (key === "leave") {
      const leaveTypeNameMap = await getLeaveTypeNameMap();
      setLeave(formatLeaveAnalytics(data, leaveTypeNameMap));
      return;
    }

    if (key === "serviceEvents") {
      const serviceEventTypeNameMap = await getServiceEventTypeNameMap();
      setServiceEvents(formatServiceEventsAnalytics(data, serviceEventTypeNameMap));
    }
  }, [getLeaveTypeNameMap, getServiceEventTypeNameMap, getWorkforceNameMaps]);

  const loadSections = useCallback(async (sectionKeys, { isRefresh = false, isInitial = false } = {}) => {
    const nextKeys = [...new Set((sectionKeys || []).filter(Boolean))];
    if (!nextKeys.length) {
      if (isInitial && mountedRef.current) setLoading(false);
      return;
    }

    const sectionRequestIds = {};
    nextKeys.forEach((key) => {
      const nextRequestId = (sectionRequestIdsRef.current[key] || 0) + 1;
      sectionRequestIdsRef.current[key] = nextRequestId;
      sectionRequestIds[key] = nextRequestId;
    });

    const initialRequestId = isInitial ? initialLoadRequestIdRef.current + 1 : null;
    if (isInitial) {
      initialLoadRequestIdRef.current = initialRequestId;
    }

    const refreshRequestId = isRefresh ? refreshRequestIdRef.current + 1 : null;
    if (isRefresh) {
      refreshRequestIdRef.current = refreshRequestId;
    }

    const isCurrentSectionRequest = (key) => (
      mountedRef.current && sectionRequestIdsRef.current[key] === sectionRequestIds[key]
    );

    if (isInitial) {
      setLoading(true);
    } else if (isRefresh) {
      setRefreshing(true);
    } else {
      setSectionLoading((current) => {
        const next = { ...current };
        nextKeys.forEach((key) => {
          next[key] = true;
        });
        return next;
      });
    }

    try {
      const results = await Promise.all(
        nextKeys.map(async (key) => {
          try {
            const response = await ANALYTICS_SECTION_CONFIG[key].request();
            return { key, data: response.data, failed: false };
          } catch {
            return { key, data: null, failed: true };
          }
        }),
      );

      const failures = [];
      for (const result of results) {
        if (!isCurrentSectionRequest(result.key)) {
          continue;
        }

        if (result.failed) {
          failures.push(result.key);
          continue;
        }

        await applySectionData(result.key, result.data);
        loadedSectionsRef.current.add(result.key);
      }

      setFailedSectionKeys((current) => {
        const next = new Set(current);
        results.forEach((result) => {
          if (!isCurrentSectionRequest(result.key)) return;
          if (result.failed) next.add(result.key);
          else next.delete(result.key);
        });
        return [...next];
      });

      if (failures.length === nextKeys.length) {
        toast.error("Failed to load analytics data");
      } else if (failures.length > 0 && isRefresh) {
        toast.error("Some analytics sections could not be refreshed");
      }
    } finally {
      if (isInitial && mountedRef.current && initialLoadRequestIdRef.current === initialRequestId) {
        setLoading(false);
      } else if (isRefresh && mountedRef.current && refreshRequestIdRef.current === refreshRequestId) {
        setRefreshing(false);
      } else {
        setSectionLoading((current) => {
          const next = { ...current };
          nextKeys.forEach((key) => {
            if (isCurrentSectionRequest(key)) {
              next[key] = false;
            }
          });
          return next;
        });
      }
    }
  }, [applySectionData]);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
    };
  }, []);

  const refreshData = useCallback(() => {
    const loadedKeys = [...loadedSectionsRef.current];
    const keysToRefresh = loadedKeys.length > 0 ? loadedKeys : TAB_SECTION_KEYS[activeTab];
    return loadSections(keysToRefresh, { isRefresh: true });
  }, [activeTab, loadSections]);

  const closeDrilldown = useCallback((open) => {
    if (open) return;
    setDrilldownState((current) => ({ ...current, open: false }));
  }, []);

  const openDrilldown = useCallback(async ({ section, dimension = "all", value = null, values = null, label, description }) => {
    const requestId = drilldownRequestIdRef.current + 1;
    drilldownRequestIdRef.current = requestId;
    const config = {
      section,
      dimension,
      value,
      values,
      label,
      description,
      key: buildAnalyticsDrilldownKey({ section, dimension, value, values }),
    };

    setDrilldownState({
      open: true,
      loading: true,
      config,
      data: null,
      error: null,
    });

    try {
      await ensureDrilldownMaps(section);
      const response = await analyticsAPI.getDrilldown({
        section,
        dimension,
        value,
        values,
        limit: DRILLDOWN_ROW_LIMIT,
      });

      if (!mountedRef.current || drilldownRequestIdRef.current !== requestId) return;

      setDrilldownState({
        open: true,
        loading: false,
        config,
        data: response.data,
        error: null,
      });
    } catch {
      if (!mountedRef.current || drilldownRequestIdRef.current !== requestId) return;

      setDrilldownState({
        open: true,
        loading: false,
        config,
        data: null,
        error: "Unable to load matching records for this drilldown.",
      });
      toast.error("Failed to load analytics drilldown");
    }
  }, [ensureDrilldownMaps]);

  useEffect(() => {
    loadSections(TAB_SECTION_KEYS.overview, { isInitial: true });
  }, [loadSections]);

  useEffect(() => {
    const keysToLoad = TAB_SECTION_KEYS[activeTab].filter((key) => !loadedSectionsRef.current.has(key));
    if (!keysToLoad.length) return;
    loadSections(keysToLoad);
  }, [activeTab, loadSections]);

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6" data-testid="analytics-dashboard-loading">
          <PageHeaderSkeleton />
          <StatGridSkeleton count={4} />
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <CardSkeleton lines={5} />
            <CardSkeleton lines={5} />
          </div>
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <CardSkeleton lines={5} />
            <CardSkeleton lines={5} />
          </div>
        </div>
      </Layout>
    );
  }

  const tabs = [
    { id: "overview",  label: "Overview",        icon: BarChart3 },
    { id: "workforce", label: "Workforce",       icon: Users },
    { id: "leave",     label: "Leave",           icon: Calendar },
    { id: "workflow",  label: "Workflow",         icon: GitBranch },
    { id: "events",    label: "Service Book Records",  icon: ClipboardList },
  ];

  return (
    <Layout>
      <div className="mx-auto w-full max-w-7xl min-w-0 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Analytics Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Comprehensive workforce, leave, and workflow analytics
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshData}
            disabled={refreshing}
            className="w-full sm:w-auto"
          >
            {refreshing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>

        <AnalyticsDataNotice failedSections={failedSections} />
        <AnalyticsInteractionHint />

        {/* Tab navigation */}
        <div className="flex flex-wrap gap-2 border-b pb-px sm:gap-1 sm:overflow-x-auto" data-testid="analytics-tabs">
          {tabs.map((tab, index) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const isOddLastTab = tabs.length % 2 === 1 && index === tabs.length - 1;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors whitespace-nowrap sm:flex-none sm:justify-start sm:rounded-t-lg sm:border-x-0 sm:border-t-0 sm:border-b-2 sm:px-4 ${
                  isOddLastTab ? "basis-full sm:basis-auto" : "basis-[calc(50%-0.25rem)] sm:basis-auto"
                } ${
                  isActive
                    ? "border-blue-200 bg-blue-50 text-blue-700 sm:border-blue-600 sm:bg-blue-50/50 sm:text-blue-600"
                    : "border-slate-200 bg-white text-muted-foreground hover:border-slate-300 hover:text-slate-700 hover:bg-slate-50 sm:border-transparent sm:bg-transparent"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab panels */}
        {activeTab === "overview" && <OverviewPanel overview={overview} workflow={workflow} openDrilldown={openDrilldown} />}
        {activeTab === "workforce" && (
          sectionLoading.workforce && !workforce
            ? <AnalyticsSectionLoader message="Loading workforce analytics..." />
            : <WorkforcePanel data={workforce} openDrilldown={openDrilldown} />
        )}
        {activeTab === "leave" && (
          sectionLoading.leave && !leave
            ? <AnalyticsSectionLoader message="Loading leave analytics..." />
            : <LeavePanel data={leave} openDrilldown={openDrilldown} />
        )}
        {activeTab === "workflow" && (
          sectionLoading.workflow && !workflow
            ? <AnalyticsSectionLoader message="Loading workflow analytics..." />
            : <WorkflowPanel data={workflow} openDrilldown={openDrilldown} />
        )}
        {activeTab === "events" && (
          sectionLoading.serviceEvents && !serviceEvents
            ? <AnalyticsSectionLoader message="Loading service event analytics..." />
            : <ServiceEventsPanel data={serviceEvents} openDrilldown={openDrilldown} />
        )}

        <AnalyticsDrilldownSheet
          state={drilldownState}
          onOpenChange={closeDrilldown}
          departmentNameMap={departmentNameMapRef.current}
          designationNameMap={designationNameMapRef.current}
          officeNameMap={officeNameMapRef.current}
          serviceNameMap={serviceNameMapRef.current}
          serviceGroupNameMap={serviceGroupNameMapRef.current}
          leaveTypeNameMap={leaveTypeNameMapRef.current}
          serviceEventTypeNameMap={serviceEventTypeNameMapRef.current}
          canOpenEmployees={canOpenEmployees}
          canOpenServiceEvents={canOpenServiceEvents}
        />
      </div>
    </Layout>
  );
};

/* ─── Overview Panel ─────────────────────────────────────────────── */

export default AnalyticsDashboardPage;
