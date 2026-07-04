import { useState } from 'react';
import { CalculatorTabNavigation } from './components/CalculatorSection';
import { PorePressureCalculator } from './components/PorePressureCalculator';
import { ElasticPropertiesCalculator } from './components/ElasticPropertiesCalculator';
import { RockStrengthCalculator } from './components/RockStrengthCalculator';
import { HorizontalStressesCalculator } from './components/HorizontalStressesCalculator';
import { WellboreStabilityCalculator } from './components/WellboreStabilityCalculator';
import { Activity, GitBranch } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('pore-pressure');

  const renderCalculator = () => {
    switch (activeTab) {
      case 'pore-pressure':
        return <PorePressureCalculator />;
      case 'overburden':
        return <PorePressureCalculator />;
      case 'elastic':
        return <ElasticPropertiesCalculator />;
      case 'rock-strength':
        return <RockStrengthCalculator />;
      case 'horizontal':
        return <HorizontalStressesCalculator />;
      case 'wellbore':
        return <WellboreStabilityCalculator />;
      default:
        return <PorePressureCalculator />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 rounded-lg p-2">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">GeomechPy Calculator</h1>
                <p className="text-xs text-gray-500">Petroleum Geomechanics Workflow Tools</p>
              </div>
            </div>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <GitBranch className="w-4 h-4" />
              GeomechPy
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Workflow Info Panel */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 mb-6 text-white">
          <h2 className="text-lg font-semibold mb-2">Complete Geomechanics Workflow</h2>
          <p className="text-blue-100 text-sm mb-4">
            Calculate all key parameters for wellbore stability analysis: pore pressure, overburden stress,
            elastic properties, rock strength, horizontal stresses, and safe mud weight windows.
          </p>
          <div className="flex flex-wrap gap-2">
            {[
              { step: 1, label: 'Pore Pressure' },
              { step: 2, label: 'Overburden Stress' },
              { step: 3, label: 'Elastic Properties' },
              { step: 4, label: 'Rock Strength' },
              { step: 5, label: 'Horizontal Stresses' },
              { step: 6, label: 'Wellbore Stability' },
            ].map((item) => (
              <div
                key={item.step}
                className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5 text-sm"
              >
                <span className="bg-white/20 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold">
                  {item.step}
                </span>
                {item.label}
              </div>
            ))}
          </div>
        </div>

        {/* Calculator Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <CalculatorTabNavigation activeTab={activeTab} setActiveTab={setActiveTab} />
          <div className="p-4">
            {renderCalculator()}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">
              GeomechPy Calculator - Petroleum Geomechanics Workflow Tools
            </p>
            <div className="text-xs text-gray-400">
              References: Zhang (2019) Applied Petroleum Geomechanics, Fjaer et al. (2008) Petroleum Related Rock Mechanics
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
