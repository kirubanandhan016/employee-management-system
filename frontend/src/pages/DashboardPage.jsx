import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { dashboardService } from "../services/dashboardService";
import { extractErrorMessage } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";
import AdminDashboard from "./AdminDashboard";
import HRDashboard from "./HRDashboard";
import EmployeeDashboard from "./EmployeeDashboard";

export default function DashboardPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await dashboardService.getOverview();
      setOverview(data);
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to load dashboard analytics"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  if (loading) return <LoadingSpinner label="Loading dashboard analytics..." />;
  if (error) return <ErrorAlert message={error} />;
  if (!overview) return null;

  if (user?.role === "admin") {
    return <AdminDashboard data={overview} />;
  }
  if (user?.role === "hr_manager") {
    return <HRDashboard data={overview} />;
  }
  return <EmployeeDashboard data={overview} onRefresh={fetchOverview} />;
}
