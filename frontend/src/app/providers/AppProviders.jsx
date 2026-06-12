import { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/modules/identity_access";
import { createQueryClient } from "@/platform/query/queryClient";
import ErrorBoundary from "@/app/layout/ErrorBoundary";
import { Toaster } from "@/shared/ui/sonner";
import { PasswordGate } from "@/app/router/guards";

const AppProviders = ({ children }) => {
  const [queryClient] = useState(createQueryClient);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <PasswordGate>{children}</PasswordGate>
          </BrowserRouter>
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default AppProviders;
