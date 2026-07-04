import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAppStore } from '../lib/store';
import {
  Loader2,
  ChevronLeft,
  ChevronRight,
  Check,
  Activity,
  Layers,
  Mountain,
  Zap,
  Target,
  CircleDot,
} from 'lucide-react';
import { PorePressureStep } from '../components/workflow/PorePressureStep';
import { ElasticPropertiesStep } from '../components/workflow/ElasticPropertiesStep';
import { RockStrengthStep } from '../components/workflow/RockStrengthStep';
import { HorizontalStressesStep } from '../components/workflow/HorizontalStressesStep';
import { WellboreStabilityStep } from '../components/workflow/WellboreStabilityStep';
import { ResultsDashboard } from '../components/workflow/ResultsDashboard';

const WORKFLOW_STEPS = [
  { id: 1, title: 'Pore Pressure & Overburden', icon: Layers, description: 'Calculate pore pressure and overburden stress' },
  { id: 2, title: 'Elastic Properties', icon: Zap, description: 'Convert velocity to dynamic and static properties' },
  { id: 3, title: 'Rock Strength', icon: Mountain, description: 'Calculate UCS, tensile strength, and friction angle' },
  { id: 4, title: 'Horizontal Stresses', icon: Target, description: 'Calculate Shmin and Shmax' },
  { id: 5, title: 'Wellbore Stability', icon: CircleDot, description: 'Calculate mud weight window' },
  { id: 6, title: 'Results', icon: Activity, description: 'View final results and export' },
];

export function WorkflowPage() {
  const { wellId } = useParams();
  const navigate = useNavigate();
  const { currentWell, setCurrentWell, currentStep, setCurrentStep, workflowSession, setWorkflowSession } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function fetchWellAndSession() {
      if (!wellId) return;
      setLoading(true);
      try {
        const { data: well, error: wellError } = await supabase
          .from('wells')
          .select('*')
          .eq('id', wellId)
          .maybeSingle();

        if (wellError) throw wellError;
        if (!well) {
          navigate('/wells');
          return;
        }

        setCurrentWell(well);

        // Check for existing workflow session
        const { data: session, error: sessionError } = await supabase
          .from('workflow_sessions')
          .select('*')
          .eq('well_id', wellId)
          .maybeSingle();

        if (sessionError) throw sessionError;
        if (session) {
          setWorkflowSession(session);
          setCurrentStep(session.current_step);
        } else {
          // Create new session
          const { data: newSession, error: createError } = await supabase
            .from('workflow_sessions')
            .insert({ well_id: wellId, current_step: 1, step_data: {} })
            .select()
            .single();

          if (createError) throw createError;
          setWorkflowSession(newSession);
          setCurrentStep(1);
        }
      } catch (err) {
        console.error('Error fetching well:', err);
        navigate('/wells');
      } finally {
        setLoading(false);
      }
    }

    fetchWellAndSession();
  }, [wellId, navigate, setCurrentWell, setWorkflowSession, setCurrentStep]);

  const handleNextStep = async (stepData: Record<string, unknown>) => {
    if (!workflowSession) return;
    setSaving(true);
    try {
      const nextStep = currentStep + 1;
      const { error } = await supabase
        .from('workflow_sessions')
        .update({
          current_step: nextStep,
          step_data: { ...workflowSession.step_data, ...stepData },
          updated_at: new Date().toISOString(),
        })
        .eq('id', workflowSession.id);

      if (error) throw error;
      setWorkflowSession({ ...workflowSession, current_step: nextStep, step_data: { ...workflowSession.step_data, ...stepData } });
      setCurrentStep(nextStep);
    } catch (err) {
      console.error('Error updating workflow:', err);
    } finally {
      setSaving(false);
    }
  };

  const handlePrevStep = async () => {
    if (!workflowSession || currentStep <= 1) return;
    setSaving(true);
    try {
      const prevStep = currentStep - 1;
      const { error } = await supabase
        .from('workflow_sessions')
        .update({
          current_step: prevStep,
          updated_at: new Date().toISOString(),
        })
        .eq('id', workflowSession.id);

      if (error) throw error;
      setWorkflowSession({ ...workflowSession, current_step: prevStep });
      setCurrentStep(prevStep);
    } catch (err) {
      console.error('Error updating workflow:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!currentWell) {
    return null;
  }

  const CurrentStepComponent = () => {
    switch (currentStep) {
      case 1:
        return <PorePressureStep onNext={handleNextStep} />;
      case 2:
        return <ElasticPropertiesStep onNext={handleNextStep} />;
      case 3:
        return <RockStrengthStep onNext={handleNextStep} />;
      case 4:
        return <HorizontalStressesStep onNext={handleNextStep} />;
      case 5:
        return <WellboreStabilityStep onNext={handleNextStep} />;
      case 6:
        return <ResultsDashboard />;
      default:
        return <PorePressureStep onNext={handleNextStep} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to={`/wells/${wellId}`} className="text-slate-400 hover:text-slate-600">
                <ChevronLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">{currentWell.name}</h1>
                <p className="text-sm text-slate-500">Wellbore Stability Workflow</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Step {currentStep} of {WORKFLOW_STEPS.length}</span>
              <div className="w-32 bg-slate-200 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-300"
                  style={{ width: `${(currentStep / WORKFLOW_STEPS.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar - Step Navigation */}
        <div className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-73px)] sticky top-[73px]">
          <nav className="p-4 space-y-1">
            {WORKFLOW_STEPS.map((step) => {
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              const Icon = step.icon;

              return (
                <button
                  key={step.id}
                  onClick={() => isCompleted && setCurrentStep(step.id)}
                  className={`w-full flex items-start gap-3 p-3 rounded-xl transition-colors ${
                    isActive
                      ? 'bg-primary-50 border-2 border-primary-200'
                      : isCompleted
                      ? 'hover:bg-slate-50 cursor-pointer'
                      : 'opacity-60 cursor-not-allowed'
                  }`}
                  disabled={!isCompleted && !isActive}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isActive
                      ? 'bg-primary-500 text-white'
                      : isCompleted
                      ? 'bg-emerald-100 text-emerald-600'
                      : 'bg-slate-100 text-slate-400'
                  }`}>
                    {isCompleted ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>
                  <div className="text-left">
                    <p className={`text-sm font-medium ${
                      isActive ? 'text-primary-700' : isCompleted ? 'text-slate-900' : 'text-slate-500'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{step.description}</p>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6 lg:p-8">
          <div className="max-w-4xl">
            {/* Step Header */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                {(() => {
                  const StepIcon = WORKFLOW_STEPS[currentStep - 1]?.icon || Activity;
                  return <StepIcon className="w-6 h-6 text-primary-600" />;
                })()}
                <h2 className="text-xl font-semibold text-slate-900">
                  {WORKFLOW_STEPS[currentStep - 1]?.title}
                </h2>
              </div>
              <p className="text-slate-600">{WORKFLOW_STEPS[currentStep - 1]?.description}</p>
            </div>

            {/* Step Content */}
            <div className="card p-6">
              <CurrentStepComponent />
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-6">
              <button
                onClick={handlePrevStep}
                disabled={currentStep <= 1 || saving}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>

              {currentStep < WORKFLOW_STEPS.length && (
                <button
                  form="workflow-form"
                  type="submit"
                  disabled={saving}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                    <>
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
