import { useCallback } from "react";
import { toast } from "sonner";
import { userManagementAPI } from "@/contexts/identity";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { dedupeAuthorityCodes } from "@/contexts/admin/hooks/authorityNormalization";
import {
  assignRole,
  revokeRole,
} from "@/contexts/access_control";

const useAdminUserActions = ({
  newUser,
  setCreateUserDialog,
  setNewUser,
  setActionReason,
  setReasonDialog,
  setConfirmDialog,
  setEditUserRoles,
  setEditUserDialog,
  editUserDialog,
  editUserRoles,
  confirmDialog,
  reasonDialog,
  actionReason,
  fetchDashboardData,
  fetchRoleChangeData,
}) => {
  const handleCreateUser = useCallback(async () => {
    if (!newUser.email || !newUser.name || !newUser.password) {
      toast.error("All fields are required");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newUser.email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    if (newUser.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    if (!/[A-Z]/.test(newUser.password) || !/[a-z]/.test(newUser.password) || !/[0-9]/.test(newUser.password)) {
      toast.error("Password must contain uppercase, lowercase, and a number");
      return;
    }

    try {
      await userManagementAPI.create(newUser);
      toast.success("User created successfully");
      setCreateUserDialog(false);
      setNewUser({ email: "", name: "", password: "", authorities: [], employee_id: "" });
      fetchDashboardData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create user"));
    }
  }, [newUser, setCreateUserDialog, setNewUser, fetchDashboardData]);

  const handleDeactivateUser = useCallback(async (user) => {
    setActionReason("");
    setReasonDialog({ open: true, action: "deactivate_user", data: user });
  }, [setActionReason, setReasonDialog]);

  const handleResetPassword = useCallback(async (user) => {
    setConfirmDialog({ open: true, action: "reset_password", data: user });
  }, [setConfirmDialog]);

  const handleEditUserRoles = useCallback((user) => {
    setEditUserRoles(dedupeAuthorityCodes(user.authorities || []));
    setEditUserDialog({ open: true, user });
  }, [setEditUserRoles, setEditUserDialog]);

  const handleSaveUserRoles = useCallback(async () => {
    if (!editUserDialog.user) return;

    try {
      const oldRoles = dedupeAuthorityCodes(editUserDialog.user.authorities || []);
      const nextRoles = dedupeAuthorityCodes(editUserRoles || []);

      let add = [];
      nextRoles.forEach((role) => {
        if (!oldRoles.includes(role)) {
          add = assignRole(add, role);
        }
      });

      let remove = [];
      oldRoles.forEach((role) => {
        if (!nextRoles.includes(role)) {
          remove = assignRole(remove, role);
        }
      });

      if (add.length && remove.length) {
        remove.forEach((role) => {
          add = revokeRole(add, role);
        });
      }

      const payload = {};
      if (add.length) payload.add = add;
      if (remove.length) payload.remove = remove;

      if (add.length || remove.length) {
        await userManagementAPI.patchAuthorities(editUserDialog.user.id, payload);
      }

      toast.success("User roles updated successfully");
      setEditUserDialog({ open: false, user: null });
      fetchDashboardData();
      fetchRoleChangeData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update roles"));
    }
  }, [editUserDialog, editUserRoles, setEditUserDialog, fetchDashboardData, fetchRoleChangeData]);

  const confirmAction = useCallback(async () => {
    const { action, data } = confirmDialog;

    try {
      if (action === "reset_password") {
        const tempPassword = `Reset${Date.now().toString(36)}!`;
        await userManagementAPI.updatePassword(data.id, tempPassword);
        toast.success(`Password reset. Temporary: ${tempPassword}`);
      }

      setConfirmDialog({ open: false, action: null, data: null });
      fetchDashboardData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Action failed"));
    }
  }, [confirmDialog, setConfirmDialog, fetchDashboardData]);

  const confirmReasonAction = useCallback(async () => {
    const trimmedReason = actionReason.trim();
    if (!trimmedReason) {
      toast.error("Reason is mandatory");
      return;
    }

    const { action, data } = reasonDialog;

    try {
      if (action === "deactivate_user") {
        await userManagementAPI.update(data.id, { is_active: false });
        toast.success("User deactivated");
      }

      setReasonDialog({ open: false, action: null, data: null });
      setActionReason("");

      fetchDashboardData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Action failed"));
    }
  }, [actionReason, reasonDialog, setReasonDialog, setActionReason, fetchDashboardData]);

  return {
    handleCreateUser,
    handleDeactivateUser,
    handleResetPassword,
    handleEditUserRoles,
    handleSaveUserRoles,
    confirmAction,
    confirmReasonAction,
  };
};

export default useAdminUserActions;
