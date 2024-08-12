import logging

from operations import KnowledgeBaseOperations

BUCKET_NAME = "arjstack-kb-data-source"

OSS_VECTOR_INDEX_NAME = "kb-oss-index"
KB_NAME = "arjstack-kb"
BEDROCK_EXECUTION_ROLE = "kb-role-bedrock-execution"
EMBEDDING_MODEL_NAME = "amazon.titan-embed-text-v1"

SERACH_TEXT = "Why is Hydrogen considered fuel of future?"
MODEL_ID = "anthropic.claude-instant-v1"

## Instantiate Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

operation = KnowledgeBaseOperations()


def create_vector_index():
    collection_name = input(f"Please input OSS Collection Name:").strip()
    vector_index_name = (
        input(f"Please input Vector Index Name [{OSS_VECTOR_INDEX_NAME}]:").strip()
        or OSS_VECTOR_INDEX_NAME
    )
    operation.create_vector_index(collection_name, vector_index_name)


def upload_data():
    bucket_name = (
        input(f"Please input S3 Bucket Name [{BUCKET_NAME}]:").strip() or BUCKET_NAME
    )
    operation.upload_document(bucket_name)


def create_knowledge_base():
    collection_name = input(f"Please input OSS Collection Name:").strip()
    vector_index_name = (
        input(f"Please input Vector Index Name [{OSS_VECTOR_INDEX_NAME}]:").strip()
        or OSS_VECTOR_INDEX_NAME
    )
    kb_name = input(f"Please input Knowldge Base Name [{KB_NAME}]:").strip() or KB_NAME
    bedrock_execution_role = (
        input(
            f"Please enter Bedrock Execution Role [{BEDROCK_EXECUTION_ROLE}]:"
        ).strip()
        or BEDROCK_EXECUTION_ROLE
    )
    embedding_model_name = (
        input(f"Please enter Embedding Model Name [{EMBEDDING_MODEL_NAME}]:").strip()
        or EMBEDDING_MODEL_NAME
    )
    operation.create_knowledge_base(
        kb_name,
        bedrock_execution_role,
        embedding_model_name,
        collection_name,
        vector_index_name,
    )

def create_kb_datasource():
    kb_id = input("Please enter Knowlegde Base Id: ").strip()
    ds_name = input(f"Please input Data source Name [{KB_NAME}]:").strip() or KB_NAME
    bucket_name = (
        input(f"Please input S3 Bucket Name [{BUCKET_NAME}]:").strip() or BUCKET_NAME
    )
    operation.create_kb_datasource(ds_name, kb_id, bucket_name)

def execute_ingestion_job():
    kb_id = input("Please enter Knowlegde Base Id: ").strip()
    kb_ds_id = input("Please enter KB Datasource Id: ").strip()
    
    operation.execute_ingestion_job(kb_id, kb_ds_id)

def test_kb_with_retrieve_and_generate():
    model_id = (
        input(f"Please input Model ID [{MODEL_ID}]:").strip()
        or MODEL_ID
    )
    kb_id = input("Please enter Knowlegde Base Id: ").strip()
    search_text = input(f"Please enter search text [{SERACH_TEXT}]: ").strip() or SERACH_TEXT
    operation.search_using_kb_with_retrieve_and_generate(model_id, kb_id, search_text)


def test_kb_with_retrieve():
    kb_id = input("Please enter Knowlegde Base Id: ").strip() 
    search_text = input(f"Please enter search text [{SERACH_TEXT}]: ").strip() or SERACH_TEXT
    operation.search_using_kb_with_retrieve(kb_id, search_text)


def list_kb_datasources():
    kb_id = input("Please enter Knowlegde Base Id: ").strip()
    
    operation.list_kb_datasources(kb_id)
    
def cleanup():
    collection_name = input(f"Please enter OSS Collection Name:").strip()
    kb_id = input("Please enter Knowlegde Base Id to delete: ").strip()
    kb_ds_id = input("Please enter KB Datasource Id to delete: ").strip()
    vector_index_name = (
        input(f"Please enter Vector Index Name to delete [{OSS_VECTOR_INDEX_NAME}]:").strip()
        or OSS_VECTOR_INDEX_NAME
    )
    
    operation.cleanup(collection_name, kb_id, kb_ds_id, vector_index_name)

def menu():
    """
    Explore Knowledge Base
    """

    print("------------ Gen AI: Knowledge Base Hands-on ------------")
    print("1. Upload Data in S3")
    print("2. Create Vector Index in OSS Collection")
    print("3. Create Knowledge Base")
    print("4. Create Datasource in Knowledge Base")
    print("5. Ingestion in Datasource (Embedding generation)")
    print("6. List Knowledge Bases")
    print("7. List KB datasources")
    print("8. Test Knowledge Base (With RetrieveAndGenerate API)")
    print("9. Test Knowledge Base (With Retrieve API)")
    print("10. Cleanup Resources")

    print("99. Exit")
    valid = False
    while not valid:
        choice = input("Please select option: ").strip()
        if choice.isnumeric():
            valid = True
            choice = int(choice)
        else:
            print(
                "Looks like you have not choosen available options. Please try again."
            )
    return choice


def main():
    choice = menu()

    while choice != 99:
        if choice == 1:
            upload_data()
        elif choice == 2:
            create_vector_index()
        elif choice == 3:
            create_knowledge_base()
        elif choice == 4:
            create_kb_datasource()
        elif choice == 5:
            execute_ingestion_job()
        elif choice == 6:
            operation.list_knowledge_bases()
        elif choice == 7:
            list_kb_datasources()
        elif choice == 8:
            test_kb_with_retrieve_and_generate()
        elif choice == 9:
            test_kb_with_retrieve()
        elif choice == 10:
            cleanup()
        else:
            print(
                "Looks like you have not choosen available options. Please try again."
            )

        choice = menu()

    logger.info("Thanks for using Knowledge Base code!!!")
    exit()


main()