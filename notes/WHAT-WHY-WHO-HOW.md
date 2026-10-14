# Draft for Assignment Template — What / Why / Who / How

Use this as a draft only. Update it after you finalise the data and visualisation.

## Domain

Australia's marine wildlife, with a focus on selected whales, dolphins, marine turtles, sharks and seals. The visualisation connects recorded occurrence evidence with biologically important behaviours and Commonwealth marine protection.

## Why

The purpose is to help a general Australian audience distinguish three ideas that are often confused: where marine animals have been recorded, where particular places are biologically important for behaviours such as migration or feeding, and where Commonwealth marine parks are located. The story supports comparison across species and helps readers see that occurrence, ecological importance and legal protection are related but not equivalent concepts.

## Who

The target audience is the average Australian viewer rather than a marine-science specialist. Technical terms such as “Biologically Important Area” and “IUCN zone” should therefore be introduced in plain language, and the charts should avoid requiring advanced statistical knowledge.

## What

Main datasets:

1. Atlas of Living Australia occurrence records for five focal marine species. Key attributes include scientific/common name, latitude, longitude, event date/month/year and state/territory.
2. DCCEEW Biologically Important Areas for protected marine species. Key attributes include species, species group, behaviour, location, season and polygon geometry.
3. DCCEEW Australian Marine Parks. Key attributes include network, reserve/park, zone, IUCN category, area in km² and polygon geometry.
4. ABS ASGS Edition 4 (2026) State/Territory boundaries for geographic context.

Derived attributes include monthly occurrence-record counts, focal-species richness by state, BIA feature counts by species/behaviour, park-area shares by zone category and normalised marine-park network metrics.

## How

The webpage uses a single scrollable storytelling layout with four principal analytical sections plus a conclusion/method section. At least three distinct map idioms are used: a point occurrence map, a state choropleth, and a categorical BIA polygon map; a fourth layered overlay map compares BIA locations with Commonwealth marine-park boundaries.

Australia-wide maps use a conic equal-area projection, chosen because Australia is a landscape-oriented regional extent at mid-latitudes and because area preservation is relevant to polygon comparisons. Interactivity is limited to meaningful species selectors and tooltips rather than turning the page into an expert exploration dashboard.

Advanced idioms include the maps, a heatmap, radial chart, treemap and parallel-coordinates plot. Basic charts are retained where they provide clearer comparison than a more complex idiom. Colour is used consistently for focal animal groups and BIA behaviours, with restrained backgrounds and annotations explaining interpretation limits.
