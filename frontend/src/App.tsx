import { Outlet } from 'react-router-dom';

function App() {
  return (
    <div className="min-h-screen bg-ink text-text">
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default App;
