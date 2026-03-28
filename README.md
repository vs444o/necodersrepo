# HelpNow

> Connecting elderly people who need a hand with helpers who want to make a difference.

---

##Demo
https://youtu.be/SP1rP5Nc334

---

## Problem Statement

Many elderly people struggle with everyday tasks — grocery shopping, cleaning, cooking, or even changing a lightbulb. At the same time, there are plenty of people willing to volunteer or offer their services for a small fee. The problem is that there is no easy, safe, and accessible way for these two groups to find each other.

**HelpNow** solves this by providing a simple platform where elderly people (Needers) can post help requests, and helpers (Workers) can browse and accept them — all with privacy and safety in mind.

---

## What is HelpNow?

HelpNow is a web platform with two sides:

- **The Needer** — an elderly person (or anyone) who needs help with daily tasks
- **The Helper** — a volunteer or paid worker who wants to assist

Needers post requests. Helpers browse a live map and a list of available tasks, then apply. The Needer reviews applicants and accepts one. Once the task is done, both sides can rate the experience.

---

## Core Features

### For the Needer
- Register an account and set up a profile with address
- Post a help request by selecting a **service category**:
  - Grocery shopping
  - Cleaning
  - Cooking
  - Transport
  - Tech help
  - Gardening
  - Other
- Optionally set a **price** they are willing to pay, or leave it blank to seek a **volunteer**
- **Privacy protection**: helpers only see the city on the map — the exact address is revealed only after the Needer approves a specific helper
- **Voice-to-text input** when creating a post, designed for elderly users who struggle with typing or have mild vision impairments — speak and the text is saved automatically
- Review applicants and **accept the best helper**
- Receive **in-app notifications** when someone applies

### For the Helper
- Register an account
- Choose between **volunteer** or **paid** tasks
- View a **live map** showing cities where help is needed (powered by OpenStreetMap + Leaflet)
- Browse posts showing: city, service category, and offered price (if any)
- See **distance from their location** to each request
- Apply for tasks that suit them
- Receive **in-app notifications** when accepted
- Mark tasks as **done** once completed

### After Task Completion
- The task is marked as completed
- Both sides leave a **rating**
- The Needer rates: quality of work and attitude of the helper

---

## How It Works

### Step-by-step for a Needer
1. Sign up and choose the "Help Needer" account type
2. Enter your address (used to show helpers your city on the map)
3. Click "Post New Request" and fill in the details — use voice-to-text if needed
4. Wait for helpers to apply — you'll get a notification
5. Review applicants and click "Accept Helper"
6. The accepted helper receives your full address and gets in touch
7. After the task, mark it as done and leave a rating

### Step-by-step for a Helper
1. Sign up and choose the "Volunteer / Worker" account type
2. Enter your address (used to calculate distances to requests)
3. Go to "Find Nearby Jobs" to see the map and list of open requests
4. Browse tasks sorted by distance and recency
5. Click "Apply" on a task that interests you
6. Wait to be accepted — you'll get a notification when chosen
7. Complete the task and mark it as done

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Django 6 |
| Database | SQLite (development) |
| Frontend | HTML, CSS, JavaScript |
| Maps | Leaflet.js + OpenStreetMap |
| Geocoding | Nominatim (OpenStreetMap) |
| Auth | Django built-in authentication |
| Voice Input | Web Speech API |
| Deployment | TBD |

---

## Safety & Privacy

- **City-only visibility**: helpers see only the city of a request, never the exact address, until they are accepted
- **Approval flow**: Needers review all applicants and manually choose who gets their address
- **Rating system**: both sides rate each other after task completion to build trust over time

### Future Plans (Full Vision)
- ID card / identity verification for all helpers
- Background check integration
- Full review and reputation system
- Emergency contact feature for elderly users
- Mobile app (iOS & Android)
- Multi-language support
- Admin moderation panel

---

## Team

**Team name:** neCoders
**Hackathon:** HackTUES

| Member | Role |
|---|---|
| Member 1 | TBD |
| Member 2 | TBD |
| Member 3 | TBD |
| Member 4 | TBD |
| Member 5 | TBD |

> We are a team of 5, all 14 years old, building this project for HackTUES.

---

## Running Locally

```bash
# Clone the repository
git clone https://github.com/vs444o/necodersrepo.git
cd necodersrepo

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up the database
python manage.py migrate

# Run the development server
python manage.py runserver
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## License

This project was built for a hackathon. All rights reserved by the neCoders team.

