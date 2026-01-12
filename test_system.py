"""
Test Script voor AI Firewall POC
Comprehensive testing van alle modules en functionaliteiten.
"""

import sys
from pathlib import Path
import traceback


def test_imports():
    """Test of alle modules importeerbaar zijn."""
    print("\n📦 Testing imports...")
    
    try:
        import pandas as pd
        print("  ✓ pandas")
        
        import numpy as np
        print("  ✓ numpy")
        
        import sklearn
        print("  ✓ scikit-learn")
        
        import xgboost as xgb
        print("  ✓ xgboost")
        
        import matplotlib
        print("  ✓ matplotlib")
        
        import seaborn
        print("  ✓ seaborn")
        
        import yaml
        print("  ✓ pyyaml")
        
        import joblib
        print("  ✓ joblib")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("\n  Run: pip install -r requirements.txt")
        return False


def test_config():
    """Test configuratie laden."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from utils import Config
        
        config = Config()
        print(f"  ✓ Config geladen")
        print(f"    - Data dir: {config.get('data.input_dir')}")
        print(f"    - Test size: {config.get('training.test_size')}")
        print(f"    - GPU enabled: {config.get('training.use_gpu')}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        traceback.print_exc()
        return False


def test_data_loading():
    """Test data loading functionaliteit."""
    print("\n📁 Testing data loading...")
    
    try:
        from utils import Config
        from data_loading import DataLoader
        
        config = Config()
        loader = DataLoader(config)
        
        data_dir = Path(config.get('data.input_dir'))
        
        if not data_dir.exists():
            print(f"  ⚠️  Data directory niet gevonden: {data_dir}")
            print("      Plaats CSV bestanden in ml_data/MachineLearningCVE/")
            return False
        
        csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            print(f"  ⚠️  Geen CSV bestanden gevonden in {data_dir}")
            return False
        
        print(f"  ✓ Gevonden {len(csv_files)} CSV bestanden")
        
        # Test laden van eerste bestand
        df = loader.load_csv_files()
        print(f"  ✓ Data geladen: {df.shape}")
        print(f"    - Rows: {len(df)}")
        print(f"    - Columns: {len(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Data loading error: {e}")
        traceback.print_exc()
        return False


def test_feature_extraction():
    """Test feature extraction."""
    print("\n🔧 Testing feature extraction...")
    
    try:
        from utils import Config
        from data_loading import DataLoader
        from feature_extraction import FeatureExtractor
        
        config = Config()
        loader = DataLoader(config)
        extractor = FeatureExtractor(config)
        
        # Load sample data
        df = loader.load_csv_files()
        df = loader.preprocess_data(df)
        
        # Take small sample voor snelheid
        df_sample = df.head(1000)
        
        # Test feature extraction
        df_transformed = extractor.fit_transform(df_sample)
        
        print(f"  ✓ Features extracted: {df_transformed.shape}")
        print(f"    - Original: {df_sample.shape[1]} features")
        print(f"    - Transformed: {df_transformed.shape[1]} features")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Feature extraction error: {e}")
        traceback.print_exc()
        return False


def test_models_exist():
    """Test of getrainde modellen bestaan."""
    print("\n🤖 Testing model files...")
    
    try:
        from utils import Config
        
        config = Config()
        models_dir = Path(config.get('data.models_dir'))
        
        xgb_model = models_dir / 'xgboost_model_latest.pkl'
        if_model = models_dir / 'isolation_forest_model_latest.pkl'
        transformers = models_dir / 'feature_transformers.pkl'
        
        all_exist = True
        
        if xgb_model.exists():
            print(f"  ✓ XGBoost model found")
        else:
            print(f"  ✗ XGBoost model not found: {xgb_model}")
            all_exist = False
        
        if if_model.exists():
            print(f"  ✓ Isolation Forest model found")
        else:
            print(f"  ✗ Isolation Forest model not found: {if_model}")
            all_exist = False
        
        if transformers.exists():
            print(f"  ✓ Feature transformers found")
        else:
            print(f"  ✗ Feature transformers not found: {transformers}")
            all_exist = False
        
        if not all_exist:
            print("\n  ⚠️  Train modellen eerst met: python main.py train")
        
        return all_exist
        
    except Exception as e:
        print(f"  ✗ Model check error: {e}")
        return False


def test_inference():
    """Test inference functionaliteit."""
    print("\n🔍 Testing inference...")
    
    try:
        from inference import AIFirewallInference, create_example_flow
        
        # Initialiseer inference
        firewall = AIFirewallInference()
        print(f"  ✓ Inference engine geladen")
        
        # Test prediction
        flow = create_example_flow()
        result = firewall.predict_single_flow(flow)
        
        print(f"  ✓ Prediction successful")
        print(f"    - Prediction: {result['prediction']}")
        print(f"    - Score: {result['ensemble_score']:.4f}")
        print(f"    - Alert: {result['is_alert']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Inference error: {e}")
        traceback.print_exc()
        return False


def test_gpu_availability():
    """Test GPU beschikbaarheid voor XGBoost."""
    print("\n🎮 Testing GPU availability...")
    
    try:
        import xgboost as xgb
        
        # Check XGBoost versie
        print(f"  XGBoost version: {xgb.__version__}")
        
        # Test GPU
        try:
            # Probeer GPU device te maken
            import numpy as np
            from xgboost import DMatrix
            
            data = np.random.rand(100, 10)
            labels = np.random.randint(2, size=100)
            
            dtrain = DMatrix(data, label=labels)
            
            params = {
                'tree_method': 'gpu_hist',
                'gpu_id': 0
            }
            
            # Probeer training met GPU
            bst = xgb.train(params, dtrain, num_boost_round=1, verbose_eval=False)
            
            print(f"  ✓ GPU available and working!")
            return True
            
        except Exception as gpu_error:
            print(f"  ⚠️  GPU not available: {gpu_error}")
            print(f"     Falling back to CPU (dit is OK)")
            return False
        
    except Exception as e:
        print(f"  ✗ GPU test error: {e}")
        return False


def run_all_tests():
    """Run alle tests."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🧪 AI FIREWALL - SYSTEM TESTS 🧪                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'Imports': test_imports(),
        'Config': test_config(),
        'Data Loading': test_data_loading(),
        'Feature Extraction': test_feature_extraction(),
        'Models Exist': test_models_exist(),
        'Inference': test_inference(),
        'GPU': test_gpu_availability()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("=" * 60)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        return 0
    elif 'Imports' not in results or not results['Imports']:
        print("\n⚠️  Critical: Install dependencies first!")
        print("   Run: pip install -r requirements.txt")
        return 1
    elif not results['Models Exist']:
        print("\n⚠️  Models not found. Train them first:")
        print("   Run: python main.py train")
        return 1
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
