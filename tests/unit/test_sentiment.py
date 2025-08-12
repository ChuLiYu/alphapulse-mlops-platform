#!/usr/bin/env python3
"""
Test script for Ollama sentiment classification.
This script verifies that Ollama LLM can classify cryptocurrency sentiment.

Before running:
1. Ensure Ollama is installed and running: `ollama serve`
2. Download Llama 3.2 model: `ollama pull llama3.2:3b`
3. Or use an existing model like `mistral:latest`
"""

import json
import re
import subprocess
import sys
import time


def classify_sentiment(text, model="llama3.2:3b", max_retries=2):
    """
    Use Ollama to classify sentiment of cryptocurrency text.

    Parameters:
    -----------
    text : str
        Text to classify
    model : str
        Ollama model to use
    max_retries : int
        Maximum number of retries if classification fails

    Returns:
    --------
    dict
        Sentiment analysis result with keys:
        - sentiment: "positive", "negative", or "neutral"
        - score: float between -1.0 and 1.0
        - confidence: float between 0.0 and 1.0
        - raw_output: raw LLM output for debugging
    """

    # Create a structured prompt for consistent JSON output
    prompt = f"""
    Analyze the sentiment of this cryptocurrency-related text.
    
    TEXT: "{text}"
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "sentiment": "positive", "negative", or "neutral",
        "score": -1.0 to 1.0 (where -1.0 is extremely negative, 0.0 is neutral, 1.0 is extremely positive),
        "confidence": 0.0 to 1.0 (how confident you are in this classification),
        "reasoning": "brief explanation of your classification"
    }}
    
    IMPORTANT: Return ONLY the JSON object, no other text.
    """

    for attempt in range(max_retries):
        try:
            # Run Ollama command
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )

            if result.returncode != 0:
                print(
                    f"  ⚠️  Ollama command failed (attempt {attempt + 1}/{max_retries}):"
                )
                print(f"     stderr: {result.stderr[:200]}")
                time.sleep(2)  # Wait before retry
                continue

            raw_output = result.stdout.strip()

            # Try to extract JSON from the output
            # LLM might add extra text before or after JSON
            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)

            if not json_match:
                print(
                    f"  ⚠️  No JSON found in output (attempt {attempt + 1}/{max_retries})"
                )
                print(f"     Raw output: {raw_output[:200]}...")
                time.sleep(2)
                continue

            json_str = json_match.group()

            # Parse JSON
            sentiment_data = json.loads(json_str)

            # Validate required fields
            required_fields = ["sentiment", "score", "confidence"]
            for field in required_fields:
                if field not in sentiment_data:
                    print(
                        f"  ⚠️  Missing field '{field}' in JSON (attempt {attempt + 1}/{max_retries})"
                    )
                    sentiment_data[field] = None

            # Validate sentiment value
            if sentiment_data["sentiment"] not in ["positive", "negative", "neutral"]:
                print(f"  ⚠️  Invalid sentiment value: {sentiment_data['sentiment']}")
                sentiment_data["sentiment"] = "neutral"

            # Validate score range
            if sentiment_data["score"] is not None:
                try:
                    score = float(sentiment_data["score"])
                    # Clamp to [-1, 1] range
                    score = max(-1.0, min(1.0, score))
                    sentiment_data["score"] = score
                except (ValueError, TypeError):
                    sentiment_data["score"] = 0.0

            # Validate confidence range
            if sentiment_data["confidence"] is not None:
                try:
                    confidence = float(sentiment_data["confidence"])
                    # Clamp to [0, 1] range
                    confidence = max(0.0, min(1.0, confidence))
                    sentiment_data["confidence"] = confidence
                except (ValueError, TypeError):
                    sentiment_data["confidence"] = 0.5

            sentiment_data["raw_output"] = raw_output[
                :500
            ]  # Store truncated raw output
            return sentiment_data

        except json.JSONDecodeError as e:
            print(
                f"  ⚠️  JSON decode error (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            print(
                f"     JSON string: {json_str[:200] if 'json_str' in locals() else 'N/A'}"
            )
            time.sleep(2)
            continue

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Ollama timeout (attempt {attempt + 1}/{max_retries})")
            time.sleep(5)  # Longer wait for timeout
            continue

        except Exception as e:
            print(
                f"  ⚠️  Unexpected error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)}"
            )
            time.sleep(2)
            continue

    # If all retries failed, return default neutral sentiment
    print(f"  ❌ All {max_retries} attempts failed, returning neutral sentiment")
    return {
        "sentiment": "neutral",
        "score": 0.0,
        "confidence": 0.0,
        "reasoning": "Classification failed after multiple attempts",
        "raw_output": "Error: Classification failed",
    }


def test_ollama_connection():
    """Test if Ollama is running and accessible."""
    print("🔍 Testing Ollama connection...")

    try:
        # Check if ollama command exists
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   ✅ Ollama version: {result.stdout.strip()}")
        else:
            print(f"   ❌ Ollama command failed: {result.stderr}")
            return False

        # List available models
        print("\n📋 Checking available models...")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)

        if result.returncode == 0:
            models_output = result.stdout.strip()
            print(f"   Available models:\n{models_output}")

            # Check if llama3.2:3b is available
            if "llama3.2:3b" in models_output:
                print("   ✅ llama3.2:3b model is available")
                recommended_model = "llama3.2:3b"
            elif "mistral:latest" in models_output:
                print("   ⚠️  llama3.2:3b not found, using mistral:latest instead")
                recommended_model = "mistral:latest"
            elif "frenchmate:latest" in models_output:
                print("   ⚠️  Using frenchmate:latest as fallback")
                recommended_model = "frenchmate:latest"
            else:
                # Get first model from list
                lines = models_output.split("\n")
                if len(lines) > 1:  # Skip header
                    first_model = lines[1].split()[0]
                    print(f"   ⚠️  Using {first_model} as fallback")
                    recommended_model = first_model
                else:
                    print("   ❌ No models found. Please download a model:")
                    print("      ollama pull llama3.2:3b")
                    return False
        else:
            print(f"   ❌ Failed to list models: {result.stderr}")
            return False

        return recommended_model

    except FileNotFoundError:
        print("   ❌ Ollama command not found. Please install Ollama:")
        print("      Visit https://ollama.com/download")
        return False
    except Exception as e:
        print(f"   ❌ Error testing Ollama: {type(e).__name__}: {str(e)}")
        return False


def run_sentiment_tests(model):
    """Run sentiment classification tests."""
    print(f"\n🧪 Running sentiment tests with model: {model}")

    # Test cases covering different sentiment types
    test_cases = [
        {
            "text": "Bitcoin to the moon! Best investment ever! 🚀",
            "expected_sentiment": "positive",
        },
        {
            "text": "BTC crashed 20% today, portfolio destroyed",
            "expected_sentiment": "negative",
        },
        {
            "text": "Bitcoin price stable at $40k, trading sideways",
            "expected_sentiment": "neutral",
        },
        {
            "text": "Just bought more BTC at the dip! This is the opportunity of a lifetime!",
            "expected_sentiment": "positive",
        },
        {
            "text": "Regulators are cracking down on crypto exchanges, this is terrible news",
            "expected_sentiment": "negative",
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected_sentiment"]

        print(f"\n  Test {i}: {text[:50]}...")
        print(f"     Expected: {expected}")

        start_time = time.time()
        result = classify_sentiment(text, model=model)
        elapsed_time = time.time() - start_time

        print(
            f"     Result: {result['sentiment']} (score: {result['score']:.2f}, confidence: {result['confidence']:.2f})"
        )
        print(f"     Time: {elapsed_time:.1f}s")

        # Check if result matches expected
        if result["sentiment"] == expected:
            print(f"     ✅ Correct!")
        else:
            print(f"     ⚠️  Mismatch (got {result['sentiment']}, expected {expected})")

        results.append(
            {
                "test": i,
                "text": text,
                "expected": expected,
                "result": result,
                "time": elapsed_time,
                "match": result["sentiment"] == expected,
            }
        )

    return results


def print_summary(results, model):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("SENTIMENT TEST SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    correct_tests = sum(1 for r in results if r["match"])
    accuracy = correct_tests / total_tests if total_tests > 0 else 0

    print(f"Model: {model}")
    print(f"Tests run: {total_tests}")
    print(f"Correct classifications: {correct_tests}")
    print(f"Accuracy: {accuracy:.1%}")

    # Calculate average response time
    avg_time = sum(r["time"] for r in results) / total_tests if total_tests > 0 else 0
    print(f"Average response time: {avg_time:.1f}s")

    # Show detailed results
    print("\nDetailed Results:")
    for r in results:
        status = "✅" if r["match"] else "⚠️"
        print(
            f"  {status} Test {r['test']}: {r['expected']} → {r['result']['sentiment']} "
            f"(score: {r['result']['score']:.2f}, time: {r['time']:.1f}s)"
        )

    print("\n" + "=" * 60)

    if accuracy >= 0.6:
        print("✅ Sentiment classification is working reasonably well!")
        print("\nNext steps:")
        print("   1. You can now integrate this into the Reddit sentiment pipeline")
        print("   2. Consider fine-tuning prompts for better accuracy")
        print("   3. Add caching to improve performance")
        return True
    else:
        print("⚠️  Sentiment classification accuracy is low")
        print("\nTroubleshooting tips:")
        print("   1. Try a different model: ollama pull mistral:latest")
        print("   2. Improve the prompt template in classify_sentiment()")
        print("   3. Check if the model supports JSON output")
        print("   4. Consider using a dedicated sentiment analysis model")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Ollama Sentiment Classification Test")
    print("=" * 60)

    # Test Ollama connection
    model = test_ollama_connection()
    if not model:
        print("\n❌ Ollama setup failed. Please fix the issues above.")
        sys.exit(1)

    # Run sentiment tests
    results = run_sentiment_tests(model)

    # Print summary
    success = print_summary(results, model)

    # Exit with appropriate code
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Test completed with warnings")
        sys.exit(1)
