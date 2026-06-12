import { useCallback, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const parsePositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(value || "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

/**
 * URL-derived table state: filters, sort, and pagination live in the query
 * string as the single source of truth. Views are shareable/bookmarkable and
 * browser back/forward moves the table through its filter history.
 *
 * Defaults are omitted from the URL; setting a filter resets the page param
 * unless that filter opts out with `resetsPage: false`.
 *
 * @param {Object}  config
 * @param {Object}  config.filters  map of stateKey -> { param, defaultValue, resetsPage? }
 * @param {Object}  [config.sort]   { fieldParam, dirParam, defaultField, defaultDir }
 * @param {string}  [config.pageParam="page"]
 */
export function useUrlTableState({ filters = {}, sort, pageParam = "page" }) {
  const location = useLocation();
  const navigate = useNavigate();

  // Filter configs are declarative and not expected to change identity per
  // render in a meaningful way; latest config is read through a ref so the
  // setter callbacks stay stable.
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const searchParams = useMemo(
    () => new URLSearchParams(location.search || ""),
    [location.search],
  );

  const values = useMemo(() => {
    const next = {};
    for (const [key, config] of Object.entries(filtersRef.current)) {
      next[key] = searchParams.get(config.param) ?? config.defaultValue;
    }
    return next;
  }, [searchParams]);

  const page = parsePositiveInt(searchParams.get(pageParam), 1);
  const sortField = sort ? searchParams.get(sort.fieldParam) || sort.defaultField : undefined;
  const sortDir = sort ? searchParams.get(sort.dirParam) || sort.defaultDir : undefined;

  const applyParams = useCallback(
    (mutate) => {
      const params = new URLSearchParams(location.search || "");
      mutate(params);
      const nextSearch = params.toString();
      const normalizedCurrent = (location.search || "").replace(/^\?/, "");
      if (nextSearch === normalizedCurrent) return;
      navigate(
        { pathname: location.pathname, search: nextSearch ? `?${nextSearch}` : "" },
        { replace: true },
      );
    },
    [location.pathname, location.search, navigate],
  );

  const setValue = useCallback(
    (key, value) => {
      const config = filtersRef.current[key];
      if (!config) return;
      applyParams((params) => {
        const normalized = value === undefined || value === null ? "" : String(value);
        if (normalized === "" || normalized === String(config.defaultValue ?? "")) {
          params.delete(config.param);
        } else {
          params.set(config.param, normalized);
        }
        if (config.resetsPage !== false) params.delete(pageParam);
      });
    },
    [applyParams, pageParam],
  );

  const setPage = useCallback(
    (value) => {
      applyParams((params) => {
        const current = parsePositiveInt(params.get(pageParam), 1);
        const next = typeof value === "function" ? value(current) : value;
        if (!next || next <= 1) params.delete(pageParam);
        else params.set(pageParam, String(next));
      });
    },
    [applyParams, pageParam],
  );

  const toggleSort = useCallback(
    (field) => {
      if (!sort) return;
      applyParams((params) => {
        const currentField = params.get(sort.fieldParam) || sort.defaultField;
        const currentDir = params.get(sort.dirParam) || sort.defaultDir;
        let nextField = field;
        let nextDir = "asc";
        if (currentField === field) {
          nextField = currentField;
          nextDir = currentDir === "asc" ? "desc" : "asc";
        }
        if (nextField === sort.defaultField) params.delete(sort.fieldParam);
        else params.set(sort.fieldParam, nextField);
        if (nextDir === sort.defaultDir) params.delete(sort.dirParam);
        else params.set(sort.dirParam, nextDir);
        params.delete(pageParam);
      });
    },
    [applyParams, pageParam, sort],
  );

  const clearFilters = useCallback(() => {
    applyParams((params) => {
      for (const config of Object.values(filtersRef.current)) {
        params.delete(config.param);
      }
      params.delete(pageParam);
    });
  }, [applyParams, pageParam]);

  return {
    values,
    setValue,
    page,
    setPage,
    sortField,
    sortDir,
    toggleSort,
    clearFilters,
  };
}
