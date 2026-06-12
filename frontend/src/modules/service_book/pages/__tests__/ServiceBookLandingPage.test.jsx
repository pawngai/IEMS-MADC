import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import ServiceBookLandingPage from "@/modules/service_book/pages/ServiceBookLandingPage";

const mockNavigate = jest.fn();
let mockPathname = "/service-book";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: mockPathname }),
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

describe("ServiceBookLandingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname = "/service-book";
  });

  test("navigates to non-portal employee directory", () => {
    render(<ServiceBookLandingPage />);

    expect(screen.getByText("Service Book")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("service-book-open-directory-btn"));

    expect(mockNavigate).toHaveBeenCalledWith("/employees");
  });

  test("navigates to portal employee directory when opened from portal route", () => {
    mockPathname = "/portal/service-book";

    render(<ServiceBookLandingPage />);

    expect(screen.getByText("Service Book")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("service-book-open-directory-btn"));

    expect(mockNavigate).toHaveBeenCalledWith("/portal/employees");
  });
});