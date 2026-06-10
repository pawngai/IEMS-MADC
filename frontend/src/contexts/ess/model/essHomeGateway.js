import { essAPI } from "@/contexts/ess/api/essApi";

export const fetchMyProfile = () => essAPI.getMyProfile();
