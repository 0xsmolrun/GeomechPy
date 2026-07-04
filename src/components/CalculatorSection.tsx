import { Calculator, Layers, Zap, Mountain, Target, Wrench } from 'lucide-react';

interface TabProps {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}

function Tab({ label, icon, active, onClick }: TabProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors rounded-t-lg border-b-2 ${
        active
          ? 'text-blue-600 border-blue-600 bg-white'
          : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

interface CalculatorTabNavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function CalculatorTabNavigation({ activeTab, setActiveTab }: CalculatorTabNavigationProps) {
  const tabs = [
    { id: 'pore-pressure', label: 'Pore Pressure', icon: <Layers className="w-4 h-4" /> },
    { id: 'overburden', label: 'Overburden Stress', icon: <Mountain className="w-4 h-4" /> },
    { id: 'elastic', label: 'Elastic Properties', icon: <Zap className="w-4 h-4" /> },
    { id: 'rock-strength', label: 'Rock Strength', icon: <Wrench className="w-4 h-4" /> },
    { id: 'horizontal', label: 'Horizontal Stresses', icon: <Target className="w-4 h-4" /> },
    { id: 'wellbore', label: 'Wellbore Stability', icon: <Calculator className="w-4 h-4" /> },
  ];

  return (
    <div className="border-b border-gray-200 bg-gray-50 px-4">
      <div className="flex overflow-x-auto">
        {tabs.map((tab) => (
          <Tab
            key={tab.id}
            {...tab}
            active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          />
        ))}
      </div>
    </div>
  );
}
