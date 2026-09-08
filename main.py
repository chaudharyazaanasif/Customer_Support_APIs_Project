import json
from collections import Counter
from fastapi import FastAPI,status
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Optional
from schemas import TicketInput
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import time
from config.static_config import mount_static_files  # import static
from config.templates_config import templates as project_templates  # import template


app = FastAPI(
    title="Customer Support API",
    description="Customer support tickets stored in tickets.json.",
)
# Mount the static files
mount_static_files(app)

logging.basicConfig(
    filename="app.logs",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    if request.client:
        client = f"{request.client.host}:{request.client.port}"
    else:
        client = "Unknown"

    try:
        # API request ko process karo
        response = await call_next(request)
        # Response ka time
        process_time = time.time() - start_time
        logger.info(
             f'{client} - "{method} {endpoint} HTTP/1.1" '
        f'{response.status_code}'
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.exception(
            f"{client}  "
            f"{method}   "
            f"{endpoint}   "
            f"{str(e)}   "
        )
        raise


@app.post("/create_ticket")
def create_tickets(ticket: TicketInput):

    with open("tickets.json", "r") as f:
        tickets = json.load(f)

    ticket_data = ticket.model_dump()
    ticket_data["id"] = len(tickets) + 1
    tickets.append(ticket_data)
    with open("tickets.json", "w") as f:
        json.dump(tickets, f, indent=4)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Ticket create ho gaya",
            "ticket_detail": ticket_data
        }
    )

@app.get("/tickets")
def get_tickets(
    customer_name: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None
):
    with open("tickets.json", 'r') as file:
        tickets = json.load(file)
    filtered_tickets = tickets

    if customer_name:
        filtered_tickets = [
            ticket for ticket in filtered_tickets
            if ticket["customer_name"].lower() == customer_name.lower()
        ]

    if status:
        filtered_tickets = [
            ticket for ticket in filtered_tickets
            if ticket["status"].lower() == status.lower()
        ]

    if priority:
        filtered_tickets = [
            ticket for ticket in filtered_tickets
            if ticket["priority"].lower() == priority.lower()
        ]

    if category:
        filtered_tickets = [
            ticket for ticket in filtered_tickets
            if ticket["category"].lower() == category.lower()
        ]

    return JSONResponse(
        status_code=200,
        content={
            "message":"api call hogaye ha",
            "response": filtered_tickets
        }

    )

@app.put("/tickets/{ticket_id}")
def update_ticket(ticket_id: int,ticket: TicketInput):
    with open("tickets.json", "r") as f:
        tickets = json.load(f)
    for ticket in tickets:
        if ticket["id"] == ticket_id:

            ticket["customer_name"] = ticket.customer_name
            ticket["status"] = ticket.status
            ticket["priority"] = ticket.priority
            ticket["category"] = ticket.category

            with open("tickets.json", "w") as f:
                json.dump(tickets, f, indent=4)

            return {
                "message": "Ticket successfully updated",
                "ticket_detail": ticket
            }

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Ticket not found"}
    )


@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    with open("tickets.json", "r") as f:
        tickets = json.load(f)
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            tickets.remove(ticket)
            with open("tickets.json", "w") as f:
                json.dump(tickets, f, indent=4)
            return {
                "message": "Ticket successfully deleted",
                "ticket_detail": ticket
            }

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Ticket not found"}
    )

@app.get("/dashboard")
async def dashboard(request: Request):
    with open("tickets.json", 'r') as file:
        tickets = json.load(file)
    #counts = Counter([t["category"] for t in tickets if "category" in t])
    #category_counts = dict(counts)
    # 3. Get total number of unique categories
    total_tickets = len(tickets)
    category_counts = Counter(ticket["category"] for ticket in tickets)
    categories=[]
    for name, count in category_counts.items():
        percentage = round((count / total_tickets) * 100,1)
        if percentage > 20:
            color = "bg-danger"
        else:
            color="bg-primary"

        categories.append({
            "name": name.replace("_", " "),
            "count": count,
            "percentage": percentage,
            "color":color
        })

    return project_templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "categories": categories,
            "total_tickets":total_tickets
        },
    )

templates = Jinja2Templates(directory="templates")
@app.get("/logs", response_class=HTMLResponse)
async def show_logs(request: Request):
    with open("app.logs", "r") as file:
        logs = file.read()

    return templates.TemplateResponse(
        name="logs.html",
        request=request,
        context={
            "logs": logs
        }
    )
