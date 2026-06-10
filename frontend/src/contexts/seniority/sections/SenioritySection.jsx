import { memo } from "react";
import { TabsContent } from "@/shared/ui/tabs";
import SeniorityListsTab from "@/contexts/seniority/components/SeniorityListsTab";
import useSeniorityAdmin from "@/contexts/seniority/hooks/useSeniorityAdmin";

const SenioritySection = ({ activeTab }) => {
  const seniority = useSeniorityAdmin();

  return (
    <TabsContent value="seniority" className="space-y-6">
      <SeniorityListsTab
        lists={seniority.lists}
        total={seniority.total}
        loading={seniority.loading}
        detail={seniority.detail}
        detailLoading={seniority.detailLoading}
        generating={seniority.generating}
        transitioning={seniority.transitioning}
        availableServices={seniority.availableServices}
        availableDesignations={seniority.availableDesignations}
        statusFilter={seniority.statusFilter}
        setStatusFilter={seniority.setStatusFilter}
        serviceFilter={seniority.serviceFilter}
        setServiceFilter={seniority.setServiceFilter}
        listTypeFilter={seniority.listTypeFilter}
        setListTypeFilter={seniority.setListTypeFilter}
        yearFilter={seniority.yearFilter}
        setYearFilter={seniority.setYearFilter}
        pagination={seniority.pagination}
        setPagination={seniority.setPagination}
        fetchLists={seniority.fetchLists}
        fetchOptions={seniority.fetchOptions}
        fetchDetail={seniority.fetchDetail}
        generateList={seniority.generateList}
        overrideRanks={seniority.overrideRanks}
        transition={seniority.transition}
        promote={seniority.promote}
        exportCSV={seniority.exportCSV}
        setDetail={seniority.setDetail}
      />
    </TabsContent>
  );
};

export default memo(SenioritySection);
