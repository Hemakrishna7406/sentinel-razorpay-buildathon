import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import Landing from './pages/Landing/Landing';
import Dashboard from './pages/Dashboard/Dashboard';
import Overview from './pages/Dashboard/Overview';

import AuditLog from './pages/Dashboard/AuditLog';
import Policies from './pages/Dashboard/Policies';
import Settings from './pages/Dashboard/Settings';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <Landing />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
        children: [
          {
            index: true,
            element: <Overview />,
          },
          {
            path: 'audit',
            element: <AuditLog />,
          },
          {
            path: 'policies',
            element: <Policies />,
          },
          {
            path: 'settings',
            element: <Settings />,
          }
        ]
      }
    ],
  },
]);
