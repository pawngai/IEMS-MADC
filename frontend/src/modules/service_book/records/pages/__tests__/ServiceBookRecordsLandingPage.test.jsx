import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import ServiceBookRecordsLandingPage from "@/modules/service_book/records/pages/ServiceBookRecordsLandingPage";

const mockNavigate = jest.fn();
let mockPathname = "/service-book/records";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: mockPathname }),
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

describe("ServiceBookRecordsLandingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname = "/service-book/records";
  });

  test("navigates to non-portal employee directory", () => {
    render(<ServiceBookRecordsLandingPage />);

    fireEvent.click(screen.getByTestId("service-records-open-directory-btn"));

    expect(mockNavigate).toHaveBeenCalledWith("/employees");
  });

  test("navigates to portal employee directory when opened from portal route", () => {
    mockPathname = "/portal/service-book/records";

    render(<ServiceBookRecordsLandingPage />);

    fireEvent.click(screen.getByTestId("service-records-open-directory-btn"));

    expect(mockNavigate).toHaveBeenCalledWith("/portal/employees");
  });
});
