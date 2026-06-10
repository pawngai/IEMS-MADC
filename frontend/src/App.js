import "@/App.css";
import AppProviders from "@/app/providers/AppProviders";
import AppRouter from "@/app/router/routes";

function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  );
}

export default App;
