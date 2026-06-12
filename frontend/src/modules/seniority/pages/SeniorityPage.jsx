import SeniorityListsTab from "@/modules/seniority/components/SeniorityListsTab";
import useSeniorityAdmin from "@/modules/seniority/hooks/useSeniorityAdmin";

const SeniorityPage = () => {
  const seniority = useSeniorityAdmin();

  return (
    <>
      <div className="space-y-6">
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
    </div>
    </>
  );
};

export default SeniorityPage;
