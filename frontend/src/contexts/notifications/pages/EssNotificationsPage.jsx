import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { ESS } from "@/shared/lib/routes";
import { essAPI } from "@/contexts/ess";
import { leaveAPI } from "@/contexts/leave";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { CardSkeleton, PageHeaderSkeleton } from "@/shared/ui/skeletons";
import { Bell, CheckCircle2, CircleAlert, Clock, RefreshCw } from "lucide-react";
import { toast } from "sonner";

const levelStyle = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  info: "bg-blue-100 text-blue-700",
  success: "bg-green-100 text-green-700",
};

const formatDateTime = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

const pickLeaveTimestamp = (leave) =>
  leave?.sanctioned_at ||
  leave?.rejected_at ||
  leave?.cancelled_at ||
  leave?.recommended_at ||
  leave?.applied_at ||
  null;

export const mapServerAction = (notification) => {
  if (notification?.action && typeof notification.action === "object") {
    const to = notification.action.to || notification.action.url || notification.action.path;
    if (!to) return null;
    return {
      label: notification.action.label || "Open",
      to,
    };
  }

  const actionUrl = notification?.action_url;
  if (!actionUrl || typeof actionUrl !== "string") return null;

  if (actionUrl === "/ess/my-leaves") {
    return { label: "Open Leave", to: ESS.LEAVE };
  }
  if (actionUrl === "/ess/profile") {
    return { label: "Open Profile", to: ESS.PROFILE };
  }

  return { label: "Open", to: actionUrl };
};

const EssNotificationsPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [myLeaves, setMyLeaves] = useState([]);
  const [serverNotifications, setServerNotifications] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      const [profileRes, leavesRes, notifsRes] = await Promise.all([
        essAPI.getMyProfile().catch(() => ({ data: null })),
        leaveAPI.listMy().catch(() => ({ data: [] })),
        essAPI.getNotifications().catch(() => ({ data: { notifications: [] } })),
      ]);
      setProfile(profileRes.data || null);
      setMyLeaves(Array.isArray(leavesRes.data) ? leavesRes.data : []);
      const raw = notifsRes.data?.notifications || notifsRes.data || [];
      setServerNotifications(Array.isArray(raw) ? raw : []);
    } catch (error) {
      toast.error("Failed to load notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const notifications = useMemo(() => {
    const list = [];
    const status = profile?.workflow_status || "DRAFT";
    const incomplete = profile && !profile?.employee_section_completed && ["DRAFT", "REJECTED"].includes(status);

    if (!profile) {
      list.push({
        id: "profile-missing",
        level: "medium",
        title: "Profile not linked",
        message: "Your user account is not linked to an employee profile yet.",
        timestamp: null,
        action: null,
      });
    } else {
      if (incomplete) {
        list.push({
          id: "profile-incomplete",
          level: "high",
          title: "Profile action required",
          message: "Complete your profile section and submit it for processing.",
          timestamp: profile.updated_at || profile.created_at || null,
          action: { label: "Open Profile", to: ESS.PROFILE },
        });
      }

      if (!incomplete) {
        const stageText = status === "LOCKED" ? "locked and finalized" : `in ${status} stage`;
        list.push({
          id: "profile-stage",
          level: status === "LOCKED" ? "success" : "info",
          title: "Profile workflow update",
          message: `Your profile is currently ${stageText}.`,
          timestamp: profile.updated_at || profile.created_at || null,
          action: { label: "Open Profile", to: ESS.PROFILE },
        });
      }
    }

    (myLeaves || []).forEach((leave) => {
      const statusText = (leave.status || "SUBMITTED").toLowerCase();
      const level =
        leave.status === "REJECTED" ? "high" :
        leave.status === "SANCTIONED" ? "success" :
        leave.status === "CANCELLED" ? "info" :
        leave.status === "RECOMMENDED" ? "info" : "medium";

      list.push({
        id: `leave-${leave.id}`,
        level,
        title: `Leave ${statusText}`,
        message: `${leave.leave_type_code} • ${leave.from_date} to ${leave.to_date}`,
        timestamp: pickLeaveTimestamp(leave),
        action: { label: "Open Leave", to: ESS.LEAVE },
      });
    });

    // Merge server-side notifications (de-duplicating by id)
    const seenIds = new Set(list.map((n) => n.id));
    (serverNotifications || []).forEach((sn) => {
      const id = sn.id || `server-${Math.random()}`;
      if (seenIds.has(id)) return;
      seenIds.add(id);
      const levelMap = { error: "high", warning: "medium", info: "info", success: "success" };
      list.push({
        id,
        level: levelMap[sn.level] || sn.level || "info",
        title: sn.title || "Notification",
        message: sn.message || "",
        timestamp: sn.timestamp || null,
        action: mapServerAction(sn),
      });
    });

    return list
      .sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0))
      .slice(0, 30);
  }, [profile, myLeaves, serverNotifications]);

  if (loading) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto space-y-6" data-testid="ess-notifications-loading">
          <PageHeaderSkeleton />
          <div className="space-y-3">
            <CardSkeleton lines={3} />
            <CardSkeleton lines={3} />
            <CardSkeleton lines={3} />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="ess-notifications-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Self-Service Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Notifications</h2>
            <p className="text-sm text-slate-500 mt-1">Recent updates and pending actions.</p>
          </div>
          <Button variant="outline" className="gap-2" onClick={load}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bell className="w-5 h-5" />
              Notification Feed
            </CardTitle>
            <CardDescription>
              {notifications.length} item{notifications.length !== 1 ? "s" : ""} available.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {notifications.length === 0 ? (
              <div className="text-sm text-slate-500 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                No notifications right now.
              </div>
            ) : (
              <div className="space-y-3">
                {notifications.map((item) => (
                  <div key={item.id} className="rounded-lg border p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <CircleAlert className="w-4 h-4 text-slate-500" />
                        <p className="font-medium text-slate-900">{item.title}</p>
                      </div>
                      <Badge className={levelStyle[item.level] || levelStyle.info}>{item.level.toUpperCase()}</Badge>
                    </div>
                    <p className="text-sm text-slate-600 mt-2">{item.message}</p>
                    <div className="flex flex-wrap items-center justify-between gap-2 mt-3">
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDateTime(item.timestamp)}
                      </p>
                      {item.action && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8"
                          onClick={() => navigate(item.action.to)}
                        >
                          {item.action.label}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default EssNotificationsPage;

