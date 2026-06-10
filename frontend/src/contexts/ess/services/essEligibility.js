import { essAPI } from "@/contexts/ess/api/essApi";
import { isServiceBookEligible } from "@/contexts/service_book";

export const getEssProfile = async () => {
  const profileRes = await essAPI.getMyProfile().catch(() => ({ data: null }));
  return profileRes?.data || null;
};

export const isRegularProfile = (profile) => {
  return isServiceBookEligible(profile);
};

export const isRegularEssEmployee = async () => {
  const profile = await getEssProfile();
  return isRegularProfile(profile);
};