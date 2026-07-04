import { useState } from 'react';
import { Calculator, AlertTriangle, CheckCircle } from 'lucide-react';
import { calculateBreakdownPressure, calculateBreakoutPressure } from '../calculations/wellboreStability';

export function WellboreStabilityCalculator() {
  const [shmax, setShmax] = useState<string>('12000');
  const [shmin, setShmin] = useState<string>('10000');
  const [porePressure, setPorePressure] = useState<string>('5000');
  const [overburdenStress, setOverburdenStress] = useState<string>('13000');
  const [ucs, setUcs] = useState<string>('8000');
  const [fang, setFang] = useState<string>('30');
  const [prSta, setPrSta] = useState<string>('0.25');
  const [tstr, setTstr] = useState<string>('500');
  const [mudWeight, setMudWeight] = useState<string>('10');

  const shmaxNum = parseFloat(shmax) || 0;
  const shminNum = parseFloat(shmin) || 0;
  const ppNum = parseFloat(porePressure) || 0;
  const obNum = parseFloat(overburdenStress) || 0;
  const ucsNum = parseFloat(ucs) || 0;
  const fangNum = parseFloat(fang) || 30;
  const prStaNum = parseFloat(prSta) || 0.25;
  const tstrNum = parseFloat(tstr) || 500;
  const mudWeightNum = parseFloat(mudWeight) || 10;

  const breakdown = calculateBreakdownPressure(shmaxNum, shminNum, ppNum, tstrNum);
  const breakout = calculateBreakoutPressure(shmaxNum, shminNum, ppNum, obNum, ucsNum, fangNum, prStaNum);

  // Convert mud weight (ppg) to psi at reference depth (using 10000 ft as reference)
  const mudPressure = mudWeightNum * 0.052 * 10000;

  const isSafe = mudPressure >= breakout && mudPressure <= breakdown;
  const safeWindow = breakdown - breakout;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calculator className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Wellbore Stability Calculator</h2>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">
            Calculate the safe mud weight window for a vertical well using the Mohr-Coulomb failure criterion.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <InputField label="Shmax (psi)" value={shmax} onChange={setShmax} />
          <InputField label="Shmin (psi)" value={shmin} onChange={setShmin} />
          <InputField label="Pore Pressure (psi)" value={porePressure} onChange={setPorePressure} />
          <InputField label="Overburden Stress (psi)" value={overburdenStress} onChange={setOverburdenStress} />
          <InputField label="UCS (psi)" value={ucs} onChange={setUcs} />
          <InputField label="Friction Angle (deg)" value={fang} onChange={setFang} />
          <InputField label="Static Poisson's Ratio" value={prSta} onChange={setPrSta} step="0.01" />
          <InputField label="Tensile Strength (psi)" value={tstr} onChange={setTstr} />
        </div>

        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Current Mud Weight Analysis</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">Mud Weight (ppg)</label>
              <input
                type="number"
                value={mudWeight}
                onChange={(e) => setMudWeight(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mt-1"
                step="0.1"
              />
            </div>
            <div className="flex-1">
              <div className="text-sm text-gray-600">Mud Pressure (at 10000 ft TVD)</div>
              <div className="text-xl font-bold text-gray-900">{mudPressure.toFixed(0)} psi</div>
            </div>
            <div className="flex-1">
              {isSafe ? (
                <div className="flex items-center gap-2 text-green-600 bg-green-100 rounded-lg px-4 py-2">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-semibold">Safe</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-red-600 bg-red-100 rounded-lg px-4 py-2">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-semibold">Unsafe</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ResultCard
            title="Breakout Pressure (Min)"
            value={breakout.toFixed(0)}
            unit="psi"
            subtitle="Shear failure limit"
            color="orange"
          />
          <ResultCard
            title="Breakdown Pressure (Max)"
            value={breakdown.toFixed(0)}
            unit="psi"
            subtitle="Tensile failure limit"
            color="red"
          />
          <ResultCard
            title="Safe Mud Window"
            value={safeWindow.toFixed(0)}
            unit="psi"
            subtitle="Operating range"
            color={safeWindow > 0 ? 'green' : 'gray'}
          />
        </div>

        <div className="mt-6">
          <MudWindowVisualization
            breakout={breakout}
            breakdown={breakdown}
            mudPressure={mudPressure}
          />
        </div>
      </div>
    </div>
  );
}

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  step?: string;
}

function InputField({ label, value, onChange, step }: InputFieldProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        step={step || 'any'}
      />
    </div>
  );
}

interface ResultCardProps {
  title: string;
  value: string;
  unit: string;
  subtitle: string;
  color: 'orange' | 'red' | 'green' | 'gray';
}

function ResultCard({ title, value, unit, subtitle, color }: ResultCardProps) {
  const colorClasses = {
    orange: 'bg-orange-50 border-orange-200',
    red: 'bg-red-50 border-red-200',
    green: 'bg-green-50 border-green-200',
    gray: 'bg-gray-100 border-gray-300',
  };

  return (
    <div className={`${colorClasses[color]} rounded-lg p-4 border`}>
      <div className="text-sm text-gray-600">{title}</div>
      <div className="text-2xl font-bold text-gray-900">
        {value} <span className="text-sm font-normal">{unit}</span>
      </div>
      <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
    </div>
  );
}

interface MudWindowVisualizationProps {
  breakout: number;
  breakdown: number;
  mudPressure: number;
}

function MudWindowVisualization({ breakout, breakdown, mudPressure }: MudWindowVisualizationProps) {
  const minPressure = Math.min(breakout * 0.9, mudPressure * 0.9);
  const maxPressure = Math.max(breakdown * 1.1, mudPressure * 1.1);
  const range = maxPressure - minPressure;

  const breakoutPos = ((breakout - minPressure) / range) * 100;
  const breakdownPos = ((breakdown - minPressure) / range) * 100;
  const mudPos = ((mudPressure - minPressure) / range) * 100;

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Mud Window Visualization</h3>
      <div className="relative h-12 bg-gradient-to-r from-orange-200 via-green-200 to-red-200 rounded-lg overflow-hidden">
        {/* Breakout line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-orange-600"
          style={{ left: `${breakoutPos}%` }}
        />
        {/* Safe zone */}
        <div
          className="absolute top-0 bottom-0 bg-green-300/50"
          style={{ left: `${breakoutPos}%`, width: `${breakdownPos - breakoutPos}%` }}
        />
        {/* Breakdown line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-600"
          style={{ left: `${breakdownPos}%` }}
        />
        {/* Mud pressure indicator */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-blue-900 transform -translate-x-1/2"
          style={{ left: `${mudPos}%` }}
        />
      </div>
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>{minPressure.toFixed(0)} psi</span>
        <span className="text-orange-600">Breakout: {breakout.toFixed(0)}</span>
        <span className="text-blue-900 font-semibold">Mud: {mudPressure.toFixed(0)}</span>
        <span className="text-red-600">Breakdown: {breakdown.toFixed(0)}</span>
        <span>{maxPressure.toFixed(0)} psi</span>
      </div>
    </div>
  );
}
