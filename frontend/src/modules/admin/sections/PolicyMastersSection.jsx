import { memo, useEffect } from "react";
import { TabsContent } from "@/shared/ui/tabs";
import PolicyMastersTab from "@/modules/admin/components/PolicyMastersTab";
import MasterDialogs from "@/modules/admin/components/MasterDialogs";
import usePolicyMasterAdmin from "@/modules/admin/hooks/usePolicyMasterAdmin";

const PolicyMastersSection = ({ activeTab, getRuleBadge }) => {
  const masters = usePolicyMasterAdmin();

  useEffect(() => {
    if (activeTab === "policy-masters") {
      masters.preloadMasterCounts();
    }
  }, [activeTab, masters.preloadMasterCounts]);

  return (
    <TabsContent value="policy-masters" className="space-y-6">
      <PolicyMastersTab
        SYSTEM_MANAGED_MASTERS={masters.SYSTEM_MANAGED_MASTERS}
        selectedMasterType={masters.selectedMasterType}
        masterRecordCounts={masters.masterRecordCounts}
        loadMasterRecords={masters.loadMasterRecords}
        filteredMasterRecords={masters.filteredMasterRecords}
        masterRecords={masters.masterRecords}
        openCreateMasterDialog={masters.openCreateMasterDialog}
        masterSearch={masters.masterSearch}
        setMasterSearch={masters.setMasterSearch}
        showInactiveMasters={masters.showInactiveMasters}
        setShowInactiveMasters={masters.setShowInactiveMasters}
        masterLoading={masters.masterLoading}
        isServiceEventMaster={masters.isServiceEventMaster}
        isSelectedMasterReadOnly={masters.isSelectedMasterReadOnly}
        selectedMasterConfig={masters.selectedMasterConfig}
        getServiceEventMeta={masters.getServiceEventMeta}
        getRuleBadge={getRuleBadge}
        loadVersionHistory={masters.loadVersionHistory}
        setEditMasterData={masters.setEditMasterData}
        setEditServiceEventMeta={masters.setEditServiceEventMeta}
        setEditMasterDialog={masters.setEditMasterDialog}
        setDeprecateDialog={masters.setDeprecateDialog}
      />

      <MasterDialogs
        showVersionHistory={masters.showVersionHistory}
        setShowVersionHistory={masters.setShowVersionHistory}
        deprecateDialog={masters.deprecateDialog}
        setDeprecateDialog={masters.setDeprecateDialog}
        deprecateReason={masters.deprecateReason}
        setDeprecateReason={masters.setDeprecateReason}
        handleDeprecateMaster={masters.handleDeprecateMaster}
        editMasterDialog={masters.editMasterDialog}
        setEditMasterDialog={masters.setEditMasterDialog}
        editMasterData={masters.editMasterData}
        setEditMasterData={masters.setEditMasterData}
        isServiceEventMaster={masters.isServiceEventMaster}
        editServiceEventMeta={masters.editServiceEventMeta}
        setEditServiceEventMeta={masters.setEditServiceEventMeta}
        SERVICE_EVENT_PARTS={masters.SERVICE_EVENT_PARTS}
        submitMasterUpdate={masters.submitMasterUpdate}
        createMasterDialog={masters.createMasterDialog}
        setCreateMasterDialog={masters.setCreateMasterDialog}
        newMasterData={masters.newMasterData}
        setNewMasterData={masters.setNewMasterData}
        newMasterMetadataForm={masters.newMasterMetadataForm}
        setNewMasterMetadataForm={masters.setNewMasterMetadataForm}
        masterReferenceOptions={masters.masterReferenceOptions}
        newServiceEventMeta={masters.newServiceEventMeta}
        setNewServiceEventMeta={masters.setNewServiceEventMeta}
        SYSTEM_MANAGED_MASTERS={masters.SYSTEM_MANAGED_MASTERS}
        selectedMasterType={masters.selectedMasterType}
        submitMasterCreate={masters.submitMasterCreate}
      />
    </TabsContent>
  );
};

export default memo(PolicyMastersSection);
