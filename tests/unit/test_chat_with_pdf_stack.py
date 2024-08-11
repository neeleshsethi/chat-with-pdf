import aws_cdk as core
import aws_cdk.assertions as assertions

from chat_with_pdf.chat_with_pdf_stack import ChatWithPdfStack

# example tests. To run these tests, uncomment this file along with the example
# resource in chat_with_pdf/chat_with_pdf_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ChatWithPdfStack(app, "chat-with-pdf")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
