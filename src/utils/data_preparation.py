import os
import json
import sys
import random

def load_dataset(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_dataset(dataset, file_path):
    with open(file_path, 'w') as f:
        json.dump(dataset, f, indent=4)

def tokenize_data(data, tokenizer):
    return [{'input': tokenizer(item['code']), 'output': tokenizer(item.get('docstring', ''))} for item in data]

def split_data(data, train_size=0.8, val_size=0.1):
    """Split data into train/val/test sets"""
    random.seed(42)  # For reproducibility
    random.shuffle(data)
    
    n = len(data)
    train_end = int(n * train_size)
    val_end = train_end + int(n * val_size)
    
    train = data[:train_end]
    val = data[train_end:val_end]
    test = data[val_end:]
    
    return train, val, test

def simple_tokenizer(text):
    """Simple tokenizer that splits text by spaces"""
    return text.split()

def prepare_data(input_file, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    dataset = load_dataset(input_file)
    
    # Process the dataset based on structure
    processed_data = []
    for item in dataset:
        if 'code_diff' in item:  # Code review dataset
            processed_item = {
                'input': simple_tokenizer(item['code_diff']),
                'output': [comment['comment'] for comment in item['review_comments']],
                'metadata': {
                    'repository': item['repository'],
                    'language': item['language'],
                    'merged': item['merged']
                }
            }
        else:  # Code-doc dataset
            processed_item = {
                'input': simple_tokenizer(item['code']),
                'output': simple_tokenizer(item['docstring']),
                'metadata': {
                    'function': item['function'],
                    'language': item['language']
                }
            }
        processed_data.append(processed_item)
    
    # Split data into train/val/test
    train, val, test = split_data(processed_data)
    
    # Save splits
    save_dataset(train, os.path.join(output_dir, 'train.json'))
    save_dataset(val, os.path.join(output_dir, 'val.json'))
    save_dataset(test, os.path.join(output_dir, 'test.json'))
    
    print(f"Data processing complete:")
    print(f"  Train: {len(train)} samples")
    print(f"  Val: {len(val)} samples")
    print(f"  Test: {len(test)} samples")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python data_preparation.py <input_file> <output_dir>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    prepare_data(input_file, output_dir)
