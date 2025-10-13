#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Learning System Statistics Viewer
==================================

Command-line tool to view scraper learning system statistics and performance.

Usage:
    python -m pokertool.view_learning_stats [--detailed] [--reset]
"""

import sys
import argparse
from pathlib import Path

try:
    from pokertool.modules.scraper_learning_system import ScraperLearningSystem
except ImportError:
    from modules.scraper_learning_system import ScraperLearningSystem


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def view_learning_stats(detailed: bool = False):
    """View learning system statistics."""
    print_header("🧠 SCRAPER LEARNING SYSTEM - STATISTICS VIEWER")

    # Load learning system
    try:
        learning = ScraperLearningSystem()
    except Exception as e:
        print(f"\n❌ Error: Could not load learning system: {e}")
        print(f"\nStorage location: {Path.home() / '.pokertool' / 'learning'}")
        return 1

    # Get report
    report = learning.get_learning_report()

    # Environment Profiles
    print_section("📊 Environment Profiles")
    env_profiles = report['environment_profiles']

    if env_profiles['total'] == 0:
        print("   No environment profiles yet. The system will learn as you use it.")
    else:
        print(f"   Total Environments: {env_profiles['total']}")
        print()

        for i, profile in enumerate(env_profiles['profiles'][:10], 1):  # Show top 10
            print(f"   {i}. {profile['environment']}")
            print(f"      Success Rate: {profile['success_rate']:.1%} ({profile['attempts']} attempts)")
            print(f"      Avg Time: {profile['avg_time_ms']:.1f}ms")
            print(f"      Detection Threshold: {profile['detection_threshold']:.2f}")

            if detailed:
                print()

        if len(env_profiles['profiles']) > 10:
            print(f"\n   ... and {len(env_profiles['profiles']) - 10} more environments")

    # OCR Strategy Performance
    print_section("🎯 OCR Strategy Performance")
    ocr_strats = report['ocr_strategies']

    if not ocr_strats:
        print("   No OCR strategies tracked yet.")
    else:
        for ext_type, strategies in ocr_strats.items():
            print(f"\n   📝 {ext_type.upper()}")
            for i, strat in enumerate(strategies, 1):
                print(f"      {i}. {strat['strategy_id']}")
                print(f"         Success Rate: {strat['success_rate']:.1%}")
                print(f"         Attempts: {strat['attempts']}")
                print(f"         Avg Time: {strat['avg_time_ms']:.1f}ms")

    # Adaptive Parameters
    print_section("⚙️ Adaptive Parameters")
    params = report['adaptive_parameters']
    print(f"   Detection Threshold: {params['detection_threshold']:.2f}")
    print(f"   Card Area Range: {params['min_card_area']:.0f} - {params['max_card_area']:.0f}")
    print(f"   Card Aspect Ratio: {params['card_aspect_min']:.2f} - {params['card_aspect_max']:.2f}")
    print(f"   OCR Scale Factor: {params['ocr_scale_factor']:.1f}x")

    # Recent Performance
    print_section("📈 Recent Performance")
    recent = report['recent_performance']

    if not recent:
        print("   No recent detection data.")
    else:
        print(f"   Sample Size: {recent['sample_size']} detections")
        print(f"   Success Rate: {recent['success_rate']:.1%}")
        if recent.get('avg_confidence'):
            print(f"   Avg Confidence: {recent['avg_confidence']:.1%}")
        print(f"   Avg Time: {recent['avg_time_ms']:.1f}ms")

    # CDP Learning
    print_section("🎓 CDP-Based Learning (Ground Truth Comparison)")
    cdp_stats = report['cdp_learning']

    if cdp_stats['total_cdp_samples'] == 0:
        print("   No CDP data available yet.")
        print("   Tip: Connect to Betfair Poker in Chrome with DevTools enabled for ground truth learning.")
    else:
        print(f"   Total CDP Samples: {cdp_stats['total_cdp_samples']}")
        print()

        if cdp_stats['accuracy_by_type']:
            print("   Accuracy by Extraction Type:")
            for ext_type, stats in cdp_stats['accuracy_by_type'].items():
                print(f"      • {ext_type}: {stats['avg_accuracy']:.1%}")
                print(f"        Range: {stats['min_accuracy']:.1%} - {stats['max_accuracy']:.1%}")
                print(f"        Samples: {stats['sample_count']}")
                print()

    # User Feedback
    print_section("📝 User Feedback & Corrections")
    feedback = report['user_feedback']

    if feedback['total_feedback'] == 0:
        print("   No user feedback recorded yet.")
    else:
        print(f"   Total Feedback: {feedback['total_feedback']}")
        print(f"   Correction Rate: {feedback['correction_rate']:.1%}")
        print()

        if feedback.get('corrections_by_type'):
            print("   Corrections by Type:")
            for ext_type, count in feedback['corrections_by_type'].items():
                correct_count = feedback['correct_by_type'].get(ext_type, 0)
                total = count + correct_count
                error_rate = count / total if total > 0 else 0
                print(f"      • {ext_type}: {count} corrections ({error_rate:.1%} error rate)")

    # Learned Patterns
    print_section("🔍 Learned Patterns")
    patterns = report['learned_patterns']
    print(f"   Player Names: {patterns['player_names_count']} unique names learned")

    # Storage Info
    print_section("💾 Storage Information")
    storage_dir = Path.home() / '.pokertool' / 'learning'
    print(f"   Location: {storage_dir}")

    if storage_dir.exists():
        files = list(storage_dir.glob('*.json'))
        print(f"   Files: {len(files)}")
        total_size = sum(f.stat().st_size for f in files)
        print(f"   Total Size: {total_size / 1024:.1f} KB")

    # Summary
    print_header("📊 SUMMARY")

    # Calculate overall health score
    health_score = 0
    factors = []

    if env_profiles['total'] > 0:
        avg_success = sum(p['success_rate'] for p in env_profiles['profiles']) / len(env_profiles['profiles'])
        health_score += avg_success * 40
        factors.append(f"Environment Success: {avg_success:.1%}")

    if recent:
        health_score += recent['success_rate'] * 30
        factors.append(f"Recent Success: {recent['success_rate']:.1%}")

    if cdp_stats['total_cdp_samples'] > 0:
        health_score += 20
        factors.append("CDP Learning: Active")

    if feedback['total_feedback'] > 10:
        health_score += 10
        factors.append(f"User Feedback: {feedback['total_feedback']} samples")

    print(f"\n   Overall Learning Health: {health_score:.0f}/100")
    print(f"\n   Contributing Factors:")
    for factor in factors:
        print(f"      • {factor}")

    if health_score < 30:
        print(f"\n   💡 Tip: The system needs more data to learn effectively.")
        print(f"      Continue using the scraper to improve performance.")
    elif health_score < 60:
        print(f"\n   ✓ The system is learning and adapting.")
    else:
        print(f"\n   🌟 Excellent! The system has learned well from your environment.")

    print("\n" + "=" * 80 + "\n")

    return 0


def reset_learning_data():
    """Reset all learning data."""
    print_header("🗑️ RESET LEARNING DATA")

    print("\n⚠️  WARNING: This will delete all learned data including:")
    print("   • Environment profiles")
    print("   • OCR strategy statistics")
    print("   • Adaptive parameters")
    print("   • User feedback history")
    print("   • CDP learning data")
    print("   • Learned patterns")

    response = input("\n   Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("\n   Cancelled. No data was deleted.")
        return 0

    try:
        learning = ScraperLearningSystem()
        learning.reset_learning_data()
        learning.save()

        print("\n   ✓ All learning data has been reset.")
        print("   The system will start learning from scratch on next use.")

    except Exception as e:
        print(f"\n   ❌ Error: Could not reset learning data: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='View scraper learning system statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # View learning statistics
    python -m pokertool.view_learning_stats

    # View detailed statistics
    python -m pokertool.view_learning_stats --detailed

    # Reset all learning data
    python -m pokertool.view_learning_stats --reset
        """
    )

    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed statistics'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all learning data (requires confirmation)'
    )

    args = parser.parse_args()

    try:
        if args.reset:
            return reset_learning_data()
        else:
            return view_learning_stats(detailed=args.detailed)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
