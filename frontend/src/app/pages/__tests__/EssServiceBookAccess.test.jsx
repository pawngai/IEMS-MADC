import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import EssServiceBookPage from "@/modules/service_book/pages/EssServiceBookPage";

const mockServiceBookReadScreen = jest.fn(() => (
  <div data-testid="service-book-read-screen">ServiceBookReadScreen</div>
));

jest.mock("@/modules/service_book/containers/ServiceBookReadScreen", () => ({
  __esModule: true,
  default: (props) => mockServiceBookReadScreen(props),
}));

describe("EssServiceBookPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders ServiceBookReadScreen in ESS mode", () => {
    render(<EssServiceBookPage />);

    expect(screen.getByTestId("service-book-read-screen")).toBeInTheDocument();
    expect(mockServiceBookReadScreen).toHaveBeenCalledTimes(1);
    const firstCallProps = mockServiceBookReadScreen.mock.calls[0][0];
    expect(firstCallProps).toEqual(expect.objectContaining({ essMode: true }));
  });
});
