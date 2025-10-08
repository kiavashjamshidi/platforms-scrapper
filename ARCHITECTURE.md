# System Architecture

## Overview

This document provides a detailed overview of the system architecture for the Live Streaming Data Collection Dashboard.

## Deliverables

### Core Components

- **Data Collector:** Automated collection, error handling, extensible.
- **Database:** Optimized schema, time-series data.
- **REST API:** Endpoints for live streams, search, and stats.
- **Docker:** Complete setup with health checks.

### Documentation

1. **README.md** - Complete setup and usage guide
2. **TROUBLESHOOTING.md** - Detailed troubleshooting guide
3. **This file** - System architecture documentation

### Automation & Tools

1. **start.sh** - Quick start script with checks
2. **setup-check.sh** - Prerequisites verification script
3. **Makefile** - Common commands (build, up, down, logs, etc.)
4. **Test Suite** - Basic test coverage

## Architecture Diagram

```plaintext
+-------------------+       +-------------------+       +-------------------+
|   Twitch Helix    |       |      Kick API     |       |   YouTube Live    |
|       API         |       |                  |       |       API         |
+-------------------+       +-------------------+       +-------------------+
         |                          |                          |
         v                          v                          v
+---------------------------------------------------------------+
|                   Data Collector Service                      |
|                                                               |
|  +----------------+   +----------------+   +----------------+ |
|  | Twitch Client  |   |  Kick Client   |   | YouTube Client | |
|  +----------------+   +----------------+   +----------------+ |
|                                                               |
+---------------------------------------------------------------+
         |
         v
+---------------------------------------------------------------+
|                     Data Parser & Normalizer                  |
+---------------------------------------------------------------+
         |
         v
+---------------------------------------------------------------+
|                          Database                             |
+---------------------------------------------------------------+
         |
         v
+---------------------------------------------------------------+
|                          REST API                             |
+---------------------------------------------------------------+
         |
         v
+---------------------------------------------------------------+
|                          Dashboard                            |
+---------------------------------------------------------------+
```

## Data Flow

1. **Data Collection:**
   - The Data Collector Service fetches data from Twitch, Kick, and YouTube APIs.
   - Each platform has its own client for API interaction.

2. **Data Parsing and Normalization:**
   - The collected data is parsed and normalized into a consistent format.

3. **Database Storage:**
   - The normalized data is stored in a PostgreSQL database optimized for time-series data.

4. **REST API:**
   - The REST API provides endpoints for accessing the collected data.

5. **Dashboard:**
   - The dashboard visualizes the data and provides an interface for searching and filtering streams.
