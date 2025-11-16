import uuid, time
from models import HelpRequest, KnowledgeEntry
from notifier import notify_agent_of_supervisor_reply, send_event_to_room
from database import SessionLocal
from livekit.agents import function_tool


@function_tool
async def transfer_to_human(question: str, customer_id: str):
    """When AI decides to escalate a customer query."""
    db = SessionLocal()
    try:
        req = HelpRequest(
            id=str(uuid.uuid4()),
            question=question,
            status="pending",
            created_at=time.time(),
            customer_id=customer_id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        print(f"🆘 Escalated to human: {question}")

        await send_event_to_room("supervisor_room", {
            "type": "transfer_update",
            "request_id": req.id,
            "question": question,
            "customer_id": customer_id
        })
        return f"Transferred to a human supervisor. Request ID: {req.id}"
    finally:
        db.close()


@function_tool
async def supervisor_respond(request_id: str, answer: str):
    """Supervisor replies to a customer request."""
    db = SessionLocal()
    try:
        req = db.query(HelpRequest).filter(HelpRequest.id == request_id).first()
        if not req:
            return "Invalid request ID"

        req.answer = answer
        req.status = "resolved"
        db.commit()

        # Save to knowledge base
        topic_key = req.question.lower().strip().replace(" ", "_")[:200]
        kb = db.query(KnowledgeEntry).filter_by(topic_key=topic_key).first()
        if not kb:
            db.add(KnowledgeEntry(id=str(uuid.uuid4()), topic_key=topic_key, answer=answer))
            db.commit()

        # Notify the agent
        await notify_agent_of_supervisor_reply(req.id, answer)
        print(f"✅ Supervisor replied to {request_id}")
        return "Reply sent to customer."
    finally:
        db.close()



# from models import HelpRequest, Supervisor, KnowledgeEntry
# from database import SessionLocal
# from livekit.agents import function_tool, RunContext, get_job_context
# import time, uuid


# @function_tool
# async def transfer_to_human(ctx: RunContext, customer_query: str, customer_id: str):
#     """
#     Escalate to a human supervisor when the AI doesn't know the answer.
#     Creates a HelpRequest in the DB and assigns it to the first supervisor.
#     """
#     db = SessionLocal()
#     # job = get_job_context()  # ✅ Get the current job safely

#     try:
#         supervisor = db.query(Supervisor).first()
#         if not supervisor:
#             raise Exception("No supervisor found. Please add a supervisor in the DB.")

#         help_request = HelpRequest(
#             id=str(uuid.uuid4()),
#             supervisor_id=supervisor.id,
#             customer_id=customer_id,
#             question=customer_query,
#             status="pending",
#             created_at=time.time()
#         )
#         db.add(help_request)
#         db.commit()
#         db.refresh(help_request)

#         msg = f"✅ Escalated to supervisor {supervisor.username}. A human will review your request shortly."
#         print(msg)

#         # 🎙️ Speak out loud via the agent
#         # await job.output_stream.send_text(msg)

#         return {
#             "message": msg,
#             "help_request_id": help_request.id
#         }

#     except Exception as e:
#         err_msg = f"❌ Error in transfer_to_human: {e}"
#         print(err_msg)
#         await job.output_stream.send_text(err_msg)
#         return {"error": str(e)}

#     finally:
#         db.close()


# @function_tool
# async def supervisor_respond(ctx: RunContext, help_request_id: str, response: str):
#     """
#     Supervisor responds to a customer's help request.
#     Updates the help request and adds new knowledge to the KB.
#     Then, the AI will read the supervisor's response aloud to the customer.
#     """
#     db = SessionLocal()
#     # job = get_job_context()  # ✅ Get current LiveKit session

#     try:
#         help_request = db.query(HelpRequest).filter(HelpRequest.id == help_request_id).first()
#         if not help_request:
#             raise Exception("Help request not found.")

#         help_request.answer = response
#         help_request.status = "resolved"
#         help_request.resolved_at = time.time()

#         print(f"[Supervisor→Customer {help_request.customer_id}]: {response}")

#         kb_entry = KnowledgeEntry(
#             topic_key=str(uuid.uuid4()),
#             question=help_request.question,
#             answer=response,
#             verified_by=help_request.supervisor_id,
#             timestamp=time.time()
#         )
#         db.add(kb_entry)
#         db.commit()

#         msg = "✅ Supervisor response saved and knowledge base updated."
#         print(msg)

#         # 🎙️ Let AI speak the supervisor’s reply
#         spoken_reply = f"The supervisor replied: {response}"
#         # await job.output_stream.send_text(spoken_reply)

#         return {"message": msg, "spoken_reply": response}

#     except Exception as e:
#         err_msg = f"❌ Error in supervisor_respond: {e}"
#         print(err_msg)
#         # await job.output_stream.send_text(err_msg)
#         return {"error": str(e)}

#     finally:
#         db.close()
