import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from omegaconf import DictConfig, OmegaConf

from src.training.train import CodeModelTrainer, load_config


class TestCodeModelTrainer:
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing"""
        config = OmegaConf.create({
            "seed": 42,
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "model": {
                "name": "facebook/bart-base",
                "cache_dir": None,
                "trust_remote_code": False
            },
            "peft": {
                "use_peft": True,
                "r": 8,
                "lora_alpha": 32,
                "lora_dropout": 0.1,
                "target_modules": ["q_proj", "v_proj"],
                "bias": "none"
            },
            "data": {
                "train_path": "data/train.json",
                "val_path": "data/val.json", 
                "test_path": "data/test.json",
                "max_length": 512,
                "padding": "max_length",
                "truncation": True
            },
            "training": {
                "output_dir": "outputs/test",
                "num_train_epochs": 1,
                "per_device_train_batch_size": 2,
                "per_device_eval_batch_size": 2,
                "gradient_accumulation_steps": 1,
                "learning_rate": 5e-5,
                "weight_decay": 0.01,
                "warmup_steps": 100,
                "logging_steps": 10,
                "eval_steps": 50,
                "save_steps": 100,
                "evaluation_strategy": "steps",
                "save_strategy": "steps",
                "load_best_model_at_end": True,
                "metric_for_best_model": "eval_loss",
                "greater_is_better": False,
                "remove_unused_columns": False,
                "dataloader_num_workers": 0,
                "fp16": False,
                "gradient_checkpointing": False,
                "save_total_limit": 2
            },
            "generation": {
                "max_new_tokens": 50,
                "num_beams": 4,
                "do_sample": False,
                "early_stopping": True
            },
            "mlflow": {
                "tracking_uri": "file:./mlruns",
                "experiment_name": "test_experiment",
                "run_name": None,
                "log_model": False
            }
        })
        return config
    
    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create sample training data"""
        train_data = [
            {"input": ["def", "add", "(", "a", ",", "b", "):"], "output": ["return", "a", "+", "b"]},
            {"input": ["def", "subtract", "(", "x", ",", "y", "):"], "output": ["return", "x", "-", "y"]},
        ]
        val_data = [
            {"input": ["def", "multiply", "(", "a", ",", "b", "):"], "output": ["return", "a", "*", "b"]},
        ]
        test_data = [
            {"input": ["def", "divide", "(", "x", ",", "y", "):"], "output": ["return", "x", "/", "y"]},
        ]
        
        # Save to temporary files
        train_path = tmp_path / "train.json"
        val_path = tmp_path / "val.json"
        test_path = tmp_path / "test.json"
        
        train_path.write_text(json.dumps(train_data))
        val_path.write_text(json.dumps(val_data))
        test_path.write_text(json.dumps(test_data))
        
        return str(train_path), str(val_path), str(test_path)
    
    def test_init(self, mock_config):
        """Test CodeModelTrainer initialization"""
        trainer = CodeModelTrainer(mock_config)
        
        assert trainer.config == mock_config
        assert trainer.tokenizer is None
        assert trainer.model is None
        assert trainer.train_dataset is None
        assert trainer.val_dataset is None
        assert trainer.test_dataset is None
    
    @patch('src.training.train.AutoTokenizer')
    @patch('src.training.train.AutoModelForSeq2SeqLM')
    def test_load_tokenizer_and_model(self, mock_model_cls, mock_tokenizer_cls, mock_config):
        """Test loading tokenizer and model"""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "<eos>"
        mock_tokenizer.__len__ = Mock(return_value=50000)  # Mock tokenizer length
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
        
        mock_model = Mock()
        mock_model.num_parameters.return_value = 1000000
        mock_model_cls.from_pretrained.return_value = mock_model
        
        trainer = CodeModelTrainer(mock_config)
        
        # Act
        trainer.load_tokenizer_and_model()
        
        # Assert
        assert trainer.tokenizer == mock_tokenizer
        assert trainer.model == mock_model
        assert trainer.tokenizer.pad_token == "<eos>"
        mock_model.resize_token_embeddings.assert_called_once_with(50000)
    
    @patch('src.training.train.get_peft_model')
    @patch('src.training.train.prepare_model_for_kbit_training')
    def test_setup_peft_enabled(self, mock_prepare, mock_get_peft, mock_config):
        """Test PEFT setup when enabled"""
        trainer = CodeModelTrainer(mock_config)
        original_model = Mock()
        trainer.model = original_model
        
        mock_peft_model = Mock()
        mock_peft_model.parameters.return_value = [Mock(requires_grad=True, numel=lambda: 1000)]
        mock_get_peft.return_value = mock_peft_model
        
        # Act
        trainer.setup_peft()
        
        # Assert
        mock_prepare.assert_called_once_with(original_model)
        mock_get_peft.assert_called_once()
        assert trainer.model == mock_peft_model
    
    def test_setup_peft_disabled(self, mock_config):
        """Test PEFT setup when disabled"""
        mock_config.peft.use_peft = False
        trainer = CodeModelTrainer(mock_config)
        trainer.model = Mock()
        
        # Act
        trainer.setup_peft()
        
        # Assert - model should remain unchanged
        assert trainer.model is not None
    
    def test_load_datasets(self, mock_config, sample_data):
        """Test loading and preprocessing datasets"""
        train_path, val_path, test_path = sample_data
        
        # Update config with sample data paths
        mock_config.data.train_path = train_path
        mock_config.data.val_path = val_path
        mock_config.data.test_path = test_path
        
        trainer = CodeModelTrainer(mock_config)
        
        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}
        trainer.tokenizer = mock_tokenizer
        
        # Act
        trainer.load_datasets()
        
        # Assert
        assert trainer.train_dataset is not None
        assert trainer.val_dataset is not None
        assert trainer.test_dataset is not None
        assert len(trainer.train_dataset) == 2
        assert len(trainer.val_dataset) == 1
        assert len(trainer.test_dataset) == 1
    
    def test_compute_metrics(self, mock_config):
        """Test compute_metrics function"""
        trainer = CodeModelTrainer(mock_config)
        
        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.batch_decode.side_effect = [
            ["return a + b", "return x - y"],  # predictions
            ["return a + b", "return x * y"]   # labels
        ]
        mock_tokenizer.pad_token_id = 0
        trainer.tokenizer = mock_tokenizer
        
        # Mock eval_pred
        predictions = [[1, 2, 3], [4, 5, 6]]
        labels = [[1, 2, 3], [7, 8, 9]]
        eval_pred = (predictions, labels)
        
        # Act
        metrics = trainer.compute_metrics(eval_pred)
        
        # Assert
        assert "exact_match" in metrics
        assert isinstance(metrics["exact_match"], float)
        assert 0 <= metrics["exact_match"] <= 1


def test_load_config(tmp_path):
    """Test configuration loading"""
    # Create a temporary config file
    config_data = {
        "model": {"name": "test-model"},
        "training": {"epochs": 5}
    }
    
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
    
    # Test loading config
    config = load_config(str(config_path))
    
    assert config.model.name == "test-model"
    assert config.training.epochs == 5


def test_load_config_with_overrides(tmp_path):
    """Test configuration loading with overrides"""
    # Create a temporary config file
    config_data = {
        "model": {"name": "test-model"},
        "training": {"epochs": 5}
    }
    
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
    
    # Test loading config with overrides
    overrides = ["training.epochs=10", "model.name=new-model"]
    config = load_config(str(config_path), overrides)
    
    assert config.model.name == "new-model"
    assert config.training.epochs == 10
