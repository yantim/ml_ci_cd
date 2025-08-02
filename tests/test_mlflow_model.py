import json
import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from src.serving.mlflow_model import CodeGenerationModel, save_model_as_pyfunc, load_pyfunc_model


class TestCodeGenerationModel:
    
    @pytest.fixture
    def mock_model(self):
        """Mock CodeGenerationModel for testing"""
        model = CodeGenerationModel()
        model.device = "cpu"
        model.tokenizer = Mock()
        model.model = Mock()
        model.generation_config = {
            "max_new_tokens": 50,
            "num_beams": 4,
            "do_sample": False,
            "early_stopping": True,
            "pad_token_id": 0
        }
        return model
    
    @patch('torch.cuda.is_available')
    @patch('src.serving.mlflow_model.AutoTokenizer')
    @patch('src.serving.mlflow_model.AutoModelForSeq2SeqLM')
    def test_load_context(self, mock_model_cls, mock_tokenizer_cls, mock_cuda):
        """Test loading model context"""
        # Arrange
        mock_cuda.return_value = False
        mock_context = Mock()
        mock_context.artifacts = {"model": "/fake/path"}
        
        mock_tokenizer = Mock()
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
        
        mock_model = Mock()
        mock_model_cls.from_pretrained.return_value = mock_model
        
        # Create temporary config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            with open(config_path, 'w') as f:
                json.dump({"test": "config"}, f)
            
            mock_context.artifacts = {"model": temp_dir}
            
            code_model = CodeGenerationModel()
            
            # Act
            code_model.load_context(mock_context)
            
            # Assert
            assert code_model.tokenizer == mock_tokenizer
            assert code_model.model == mock_model
            mock_model.to.assert_called_once()
            mock_model.eval.assert_called_once()
    
    def test_predict_dataframe_input(self, mock_model):
        """Test predict with DataFrame input"""
        # Arrange
        input_df = pd.DataFrame({"input": ["def test():"]})
        mock_model.tokenizer.encode.return_value = Mock()
        mock_model.tokenizer.encode.return_value.to.return_value = Mock()
        mock_model.model.generate.return_value = [Mock()]
        mock_model.tokenizer.decode.return_value = "generated code"
        
        with patch('torch.no_grad'), patch('torch.tensor'):
            # Act
            predictions = mock_model.predict(None, input_df)
            
            # Assert
            assert predictions == ["generated code"]
    
    def test_predict_dict_input(self, mock_model):
        """Test predict with dictionary input"""
        # Arrange
        input_dict = {"input": ["def test():"]}
        mock_model.tokenizer.encode.return_value = Mock()
        mock_model.tokenizer.encode.return_value.to.return_value = Mock()
        mock_model.model.generate.return_value = [Mock()]
        mock_model.tokenizer.decode.return_value = "generated code"
        
        with patch('torch.no_grad'), patch('torch.tensor'):
            # Act
            predictions = mock_model.predict(None, input_dict)
            
            # Assert
            assert predictions == ["generated code"]
    
    def test_predict_list_input(self, mock_model):
        """Test predict with list input"""
        # Arrange
        input_list = ["def test():"]
        mock_model.tokenizer.encode.return_value = Mock()
        mock_model.tokenizer.encode.return_value.to.return_value = Mock()
        mock_model.model.generate.return_value = [Mock()]
        mock_model.tokenizer.decode.return_value = "generated code"
        
        with patch('torch.no_grad'), patch('torch.tensor'):
            # Act
            predictions = mock_model.predict(None, input_list)
            
            # Assert
            assert predictions == ["generated code"]
    
    def test_predict_unsupported_input(self, mock_model):
        """Test predict with unsupported input format"""
        # Arrange
        invalid_input = 123
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported input format"):
            mock_model.predict(None, invalid_input)


@patch('src.serving.mlflow_model.mlflow')
def test_save_model_as_pyfunc(mock_mlflow):
    """Test saving model as MLflow PyFunc"""
    # Arrange
    mock_model = Mock()
    mock_tokenizer = Mock()
    model_path = "/fake/model/path"
    mlflow_model_path = "/fake/mlflow/path"
    
    # Act
    save_model_as_pyfunc(
        model=mock_model,
        tokenizer=mock_tokenizer,
        model_path=model_path,
        mlflow_model_path=mlflow_model_path,
        registered_model_name="test_model"
    )
    
    # Assert
    mock_mlflow.pyfunc.save_model.assert_called_once()
    mock_mlflow.register_model.assert_called_once()


@patch('src.serving.mlflow_model.mlflow')
def test_load_pyfunc_model(mock_mlflow):
    """Test loading MLflow PyFunc model"""
    # Arrange
    model_uri = "models:/test_model/1"
    mock_model = Mock()
    mock_mlflow.pyfunc.load_model.return_value = mock_model
    
    # Act
    loaded_model = load_pyfunc_model(model_uri)
    
    # Assert
    assert loaded_model == mock_model
    mock_mlflow.pyfunc.load_model.assert_called_once_with(model_uri)
