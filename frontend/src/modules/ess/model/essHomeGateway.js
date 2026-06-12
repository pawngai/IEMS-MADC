import { essAPI } from "@/modules/ess/api/essApi";

export const fetchMyProfile = () => essAPI.getMyProfile();
