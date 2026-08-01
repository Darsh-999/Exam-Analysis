import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import Login from '../pages/Login/Login';
import ProjectsDashboard from '../pages/ProjectsDashboard/ProjectsDashboard';
import ProjectView from '../pages/ProjectView/ProjectView';
import QuestionsView from '../pages/QuestionsView/QuestionsView';
import TopicsView from '../pages/TopicsView/TopicsView';
import TrendsView from '../pages/TrendsView/TrendsView';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/projects" element={<ProjectsDashboard />} />
        <Route path="/projects/:projectId" element={<ProjectView />} />
        <Route path="/projects/:projectId/questions" element={<QuestionsView />} />
        <Route path="/projects/:projectId/topics" element={<TopicsView />} />
        <Route path="/projects/:projectId/trends" element={<TrendsView />} />
      </Route>

      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
