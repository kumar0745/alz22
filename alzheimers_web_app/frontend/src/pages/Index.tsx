import Navbar from "@/features/layout/Navbar";
import HeroSection from "@/features/layout/HeroSection";
import Footer from "@/features/layout/Footer";
import UploadSection from "@/features/upload/UploadSection";
import ClinicalPredictionForm from "@/features/clinical/ClinicalPredictionForm";
import SymptomChecker from "@/features/symptoms/SymptomChecker";
import BrainRegionAnalysis from "@/features/brain/BrainRegionAnalysis";
import ComparisonTimeline from "@/features/timeline/ComparisonTimeline";
import RiskAssessment from "@/features/risk/RiskAssessment";
import DashboardSection from "@/features/dashboard/DashboardSection";
import InfoSection from "@/features/info/InfoSection";

const Index = () => (
  <div className="min-h-screen bg-background">
    <Navbar />
    <HeroSection />
    <UploadSection />
    <ClinicalPredictionForm />
    <SymptomChecker />
    <BrainRegionAnalysis />
    <ComparisonTimeline />
    <RiskAssessment />
    <DashboardSection />
    <InfoSection />
    <Footer />
  </div>
);

export default Index;
