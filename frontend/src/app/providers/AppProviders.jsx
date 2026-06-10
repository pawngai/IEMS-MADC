import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/contexts/identity";
import ErrorBoundary from "@/app/layout/ErrorBoundary";
import { Toaster } from "@/shared/ui/sonner";
import { PasswordGate } from "@/app/router/guards";

const AppProviders = ({ children }) => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <PasswordGate>{children}</PasswordGate>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default AppProviders;
