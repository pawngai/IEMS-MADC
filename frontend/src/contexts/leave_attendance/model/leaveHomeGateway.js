import { leaveAPI } from "@/contexts/leave_attendance/api/leaveApi";

export const fetchMyLeaves = () => leaveAPI.listMy();
export const fetchPendingLeaveActions = ({ canRecommend = false, canSanction = false } = {}) => {
	const statuses = [
		canRecommend ? "SUBMITTED" : null,
		canSanction ? "RECOMMENDED" : null,
	].filter(Boolean);

	return leaveAPI.getPendingActions({ statuses });
};
