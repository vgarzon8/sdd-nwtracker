import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import AppLayout from "@/components/AppLayout";
import DashboardPage from "@/pages/DashboardPage";
import CurrenciesPage from "@/pages/CurrenciesPage";
import TagsPage from "@/pages/TagsPage";
import InstitutionsPage from "@/pages/InstitutionsPage";
import AccountsPage from "@/pages/AccountsPage";
import BalancesPage from "@/pages/BalancesPage";
import ReportsPage from "@/pages/ReportsPage";
import ImportExportPage from "@/pages/ImportExportPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    element: <AppLayout />,
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/currencies", element: <CurrenciesPage /> },
      { path: "/tags", element: <TagsPage /> },
      { path: "/institutions", element: <InstitutionsPage /> },
      { path: "/accounts", element: <AccountsPage /> },
      { path: "/balances", element: <BalancesPage /> },
      { path: "/reports", element: <ReportsPage /> },
      { path: "/import-export", element: <ImportExportPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
