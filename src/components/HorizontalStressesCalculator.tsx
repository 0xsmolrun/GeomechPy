import { useState } from 'react';
import { Target, Activity } from 'lucide-react';
import { calculatePoroelasticHorizontalStresses, getStressRegimeLabel } from '../calculations/stressCalculations';

export function HorizontalStressesCalculator() {
  const [overburdenStress, setOverburdenStress] = useState<string>('10000');
  const [porePressure, setPorePressure] = useState<string>('4700');
  const [poissonRatio, setPoissonRatio] = useState<string>('0.25');
  const [youngsModulus, setYoungsModulus] = useState<string>('2.0');
  const [biotCoefficient, setBiotCoefficient] = useState<string>('1.0');
  const [ex, setEx] = useState<string>('0.0001');
  const [ey, setEy] = useState<string>('0.009');

  const obNum = parseFloat(overburdenStress) || 0;
  const ppNum = parseFloat(porePressure) || 0;
  const prNum = parseFloat(poissonRatio) || 0.25;
  const ymNum = parseFloat(youngsModulus) || 2;
  const biotNum = parseFloat(biotCoefficient) || 1;
  const exNum = parseFloat(ex) || 0.0001;
  const eyNum = parseFloat(ey) || 0.009;

  const result = calculatePoroelasticHorizontalStresses(obNum, ppNum, prNum, ymNum, biotNum, exNum, eyNum);
  const regimeLabel = getStressRegimeLabel(result.qFactor);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Target className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Horizontal Stresses Calculator</h2>
        </div>

        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-gray-600">
            Calculate horizontal stresses using the poroelastic horizontal stress equation (Thiercelin & Plumb, 1994).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <InputField label="Overburden Stress (psi)" value={overburdenStress} onChange={setOverburdenStress} />
          <InputField label="Pore Pressure (psi)" value={porePressure} onChange={setPorePressure} />
          <InputField label="Poisson's Ratio" value={poissonRatio} onChange={setPoissonRatio} step="0.01" />
          <InputField label="Young's Modulus (Mpsi)" value={youngsModulus} onChange={setYoungsModulus} />
          <InputField label="Biot Coefficient" value={biotCoefficient} onChange={setBiotCoefficient} step="0.01" />
          <InputField label="Tectonic Strain EX" value={ex} onChange={setEx} step="0.0001" />
          <InputField label="Tectonic Strain EY" value={ey} onChange={setEy} step="0.0001" />
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ResultCard title="Shmin" value={result.shmin.toFixed(1)} unit="psi" color="blue" />
          <ResultCard title="Shmax" value={result.shmax.toFixed(1)} unit="psi" color="green" />
          <ResultCard title="Shmax/Shmin Ratio" value={result.shmaxShminRatio.toFixed(3)} unit="" color="purple" />
          <StressRegimeCard qFactor={result.qFactor} regime={regimeLabel} />
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
  color: 'blue' | 'green' | 'purple';
}

function ResultCard({ title, value, unit, color }: ResultCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className={`${colorClasses[color]} rounded-lg p-4 border`}>
      <div className="text-sm text-gray-600">{title}</div>
      <div className="text-xl font-bold text-gray-900">
        {value} <span className="text-sm font-normal">{unit}</span>
      </div>
    </div>
  );
}

interface StressRegimeCardProps {
  qFactor: number;
  regime: string;
}

function StressRegimeCard({ qFactor, regime }: StressRegimeCardProps) {
  const regimeColors: Record<string, string> = {
    'Normal Faulting': 'bg-green-100 border-green-300 text-green-800',
    'Strike-Slip': 'bg-yellow-100 border-yellow-300 text-yellow-800',
    'Reverse Faulting': 'bg-red-100 border-red-300 text-red-800',
    'Unclassified': 'bg-gray-100 border-gray-300 text-gray-800',
  };

  return (
    <div className={`${regimeColors[regime]} rounded-lg p-4 border`}>
      <div className="text-sm opacity-75">Stress Regime (Q={qFactor.toFixed(2)})</div>
      <div className="text-lg font-bold flex items-center gap-2">
        <Activity className="w-4 h-4" />
        {regime}
      </div>
    </div>
  );
}
