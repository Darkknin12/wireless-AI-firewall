"""
Main Orchestration Script voor AI Firewall POC
Eenvoudige interface voor alle functionaliteiten.
"""

import argparse
import sys
from pathlib import Path

from utils import Config, Logger


def train_models():
    """Train nieuwe modellen."""
    print("\n🔥 TRAINING MODELLEN 🔥\n")
    from train_model import AIFirewallTrainer
    
    config = Config()
    trainer = AIFirewallTrainer(config)
    trainer.train_full_pipeline()
    
    print("\n✅ Training compleet!")


def run_inference():
    """Test inference met voorbeeld flow."""
    print("\n🔍 INFERENCE TEST 🔍\n")
    from inference import AIFirewallInference, create_example_flow
    
    config = Config()
    firewall = AIFirewallInference(config=config)
    
    # Test met voorbeeld
    flow = create_example_flow()
    result = firewall.predict_single_flow(flow)
    
    print("\n📊 RESULTAAT:")
    print(f"  Prediction: {result['prediction'].upper()}")
    print(f"  Ensemble Score: {result['ensemble_score']:.4f}")
    print(f"  Confidence: {result['confidence']:.4f}")
    print(f"  Alert: {'🚨 YES' if result['is_alert'] else '✓ NO'}")
    
    if 'details' in result:
        print(f"\n  Details:")
        print(f"    XGBoost Score: {result['details']['xgboost_score']:.4f}")
        print(f"    Isolation Forest Score: {result['details']['isolation_forest_score']:.4f}")


def run_visualizations():
    """Genereer visualisaties."""
    print("\n📊 VISUALISATIES GENEREREN 📊\n")
    from visualize import FirewallVisualizer
    
    config = Config()
    visualizer = FirewallVisualizer(config)
    visualizer.generate_all_visualizations()
    
    print(f"\n✅ Visualisaties opgeslagen in: {config.get('data.output_dir')}")


def classify_csv(csv_path: str, output_path: str = None):
    """Classificeer flows van CSV bestand."""
    print(f"\n📁 CLASSIFICEREN: {csv_path} 📁\n")
    from inference import AIFirewallInference
    
    config = Config()
    firewall = AIFirewallInference(config=config)
    
    if output_path is None:
        output_path = str(Path(config.get('data.output_dir')) / 'predictions.csv')
    
    df_results = firewall.predict_from_csv(csv_path, output_path)
    
    print(f"\n✅ Classificatie compleet!")
    print(f"   Output: {output_path}")


def show_status():
    """Toon status van modellen en configuratie."""
    print("\n📋 AI FIREWALL STATUS 📋\n")
    
    config = Config()
    models_dir = Path(config.get('data.models_dir'))
    
    print("Configuratie:")
    print(f"  Data directory: {config.get('data.input_dir')}")
    print(f"  Models directory: {config.get('data.models_dir')}")
    print(f"  GPU enabled: {config.get('training.use_gpu')}")
    print(f"  Ensemble threshold: {config.get('ensemble.threshold')}")
    
    print("\nModellen:")
    xgb_model = models_dir / 'xgboost_model_latest.pkl'
    if_model = models_dir / 'isolation_forest_model_latest.pkl'
    transformers = models_dir / 'feature_transformers.pkl'
    
    print(f"  XGBoost: {'✅' if xgb_model.exists() else '❌'} {xgb_model}")
    print(f"  Isolation Forest: {'✅' if if_model.exists() else '❌'} {if_model}")
    print(f"  Transformers: {'✅' if transformers.exists() else '❌'} {transformers}")
    
    if not all([xgb_model.exists(), if_model.exists(), transformers.exists()]):
        print("\n⚠️  Modellen niet gevonden! Run eerst: python main.py train")


def main():
    """Main entry point met CLI."""
    parser = argparse.ArgumentParser(
        description='AI Firewall POC - Network Flow Classification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python main.py train                          # Train nieuwe modellen
  python main.py inference                      # Test inference
  python main.py visualize                      # Genereer visualisaties
  python main.py classify data.csv              # Classificeer CSV
  python main.py classify data.csv -o out.csv   # Classificeer met output
  python main.py status                         # Toon status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['train', 'inference', 'visualize', 'classify', 'status'],
        help='Command om uit te voeren'
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input CSV bestand (voor classify command)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output bestand voor classificatie resultaten'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'train':
            train_models()
        
        elif args.command == 'inference':
            run_inference()
        
        elif args.command == 'visualize':
            run_visualizations()
        
        elif args.command == 'classify':
            if not args.input_file:
                print("❌ Error: CSV bestand vereist voor classify command")
                print("   Gebruik: python main.py classify <csv_file>")
                sys.exit(1)
            classify_csv(args.input_file, args.output)
        
        elif args.command == 'status':
            show_status()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🔥 AI FIREWALL PROOF OF CONCEPT 🔥              ║
║                                                              ║
║           Network Flow Classification System                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    main()
