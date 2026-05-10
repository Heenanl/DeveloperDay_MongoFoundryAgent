# Insurance Claim Agent — Sample Scenarios

This document presents five end-to-end claim scenarios that exercise the Filing Agent and Assessment Agent pipelines. Each scenario includes realistic customer dialogue, step-by-step agent actions, and mock tool calls with representative JSON payloads.

---

## Scenario 1: Rear-End Collision at Stoplight

**Type:** Minor collision · Straightforward liability · Collision coverage  
**Customer:** Sarah Chen · **Policy:** POL-2024-78432  
**Damage:** Rear bumper crack, minor trunk dent  
**Injuries:** None  
**Estimated Repair:** $2,800 · **Deductible:** $500

---

### Description of the Accident

On the afternoon of March 12, 2025, Sarah Chen was stopped at a red light at the intersection of Maple Avenue and 5th Street in Portland, OR. A distracted driver in a silver Honda Civic failed to brake in time and rear-ended Sarah's 2022 Toyota Camry at approximately 15 mph. The impact cracked the rear bumper cover, caused a shallow dent in the trunk lid, and knocked one tail-light housing loose. No airbags deployed. Both drivers exited their vehicles; the other driver immediately admitted fault and exchanged insurance information. Sarah took six photos of the damage on her phone and filed a police report (Report #PPD-2025-04481).

---

### What the Customer Says

> "Hi, I was stopped at a red light on Maple and 5th this afternoon and someone hit me from behind. My rear bumper is cracked and there's a dent in my trunk. No one was hurt, thankfully. The other driver said it was totally their fault — they were looking at their phone. I got their insurance info and took some pictures. I also filed a police report. My policy number is POL-2024-78432. I'd like to get this fixed as soon as possible."

---

### What the Filing Agent Does

#### Step 1 — Validate the Policy

The Filing Agent confirms the customer's policy is active and retrieves coverage details.

```json
// MongoDB MCP: findOne on policies collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "policies",
    "filter": { "policyNumber": "POL-2024-78432" }
  }
}
```

**Response:**
```json
{
  "policyNumber": "POL-2024-78432",
  "holder": "Sarah Chen",
  "status": "active",
  "vehicle": {
    "year": 2022,
    "make": "Toyota",
    "model": "Camry",
    "vin": "4T1B11HK3NU123456"
  },
  "coverages": {
    "collision": { "deductible": 500, "limit": 50000 },
    "comprehensive": { "deductible": 250, "limit": 50000 },
    "liability": { "bodilyInjury": 100000, "propertyDamage": 50000 },
    "uninsuredMotorist": { "deductible": 250, "limit": 50000 }
  },
  "premiumStatus": "current"
}
```

#### Step 2 — Analyze Uploaded Damage Photos

The Filing Agent sends each uploaded photo through the ImageAnalyzer tool to detect damage regions and estimate severity.

```json
// ImageAnalyzer: Analyze damage photo 1 of 3
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-rear-bumper-01>",
    "vehicleContext": {
      "year": 2022,
      "make": "Toyota",
      "model": "Camry"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "rear_bumper_cover",
      "damageType": "crack",
      "severity": "moderate",
      "confidenceScore": 0.92,
      "boundingBox": { "x": 120, "y": 340, "w": 480, "h": 160 }
    },
    {
      "part": "trunk_lid",
      "damageType": "dent",
      "severity": "minor",
      "confidenceScore": 0.87,
      "boundingBox": { "x": 200, "y": 180, "w": 320, "h": 120 }
    }
  ],
  "overallSeverity": "minor",
  "estimatedRepairRange": { "low": 2200, "high": 3400 }
}
```

```json
// ImageAnalyzer: Analyze damage photo 2 of 3
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-taillight-02>",
    "vehicleContext": {
      "year": 2022,
      "make": "Toyota",
      "model": "Camry"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "tail_light_assembly_left",
      "damageType": "displaced",
      "severity": "minor",
      "confidenceScore": 0.89,
      "boundingBox": { "x": 60, "y": 280, "w": 140, "h": 100 }
    }
  ],
  "overallSeverity": "minor",
  "estimatedRepairRange": { "low": 150, "high": 350 }
}
```

#### Step 3 — Create the Claim Record

The Filing Agent inserts a new claim document into the `claims` collection.

```json
// MongoDB MCP: insertOne into claims collection
{
  "tool": "mongodb_mcp",
  "method": "insertOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "document": {
      "claimId": "CLM-2025-00143",
      "policyNumber": "POL-2024-78432",
      "claimant": "Sarah Chen",
      "dateOfLoss": "2025-03-12T14:30:00Z",
      "dateReported": "2025-03-12T16:45:00Z",
      "status": "filed",
      "type": "collision",
      "description": "Rear-end collision at stoplight. Vehicle was stationary at red light, struck from behind by another driver. Rear bumper cracked, trunk dented, tail-light displaced. Other driver admitted fault. Police report filed.",
      "location": {
        "intersection": "Maple Avenue & 5th Street",
        "city": "Portland",
        "state": "OR"
      },
      "policeReportNumber": "PPD-2025-04481",
      "otherParty": {
        "identified": true,
        "admittedFault": true,
        "insuranceExchanged": true
      },
      "injuries": {
        "reported": false
      },
      "damages": [
        { "part": "rear_bumper_cover", "type": "crack", "severity": "moderate" },
        { "part": "trunk_lid", "type": "dent", "severity": "minor" },
        { "part": "tail_light_assembly_left", "type": "displaced", "severity": "minor" }
      ],
      "estimatedRepairCost": 2800,
      "deductible": 500,
      "coverageApplied": "collision",
      "imageAnalysisResults": [
        { "photoId": "img-001", "overallSeverity": "minor", "confidence": 0.92 },
        { "photoId": "img-002", "overallSeverity": "minor", "confidence": 0.89 }
      ],
      "createdAt": "2025-03-12T16:45:00Z",
      "updatedAt": "2025-03-12T16:45:00Z"
    }
  }
}
```

**Response:**
```json
{
  "acknowledged": true,
  "insertedId": "65f1a2b3c4d5e6f7a8b9c0d1"
}
```

#### Step 4 — Generate Claim Embedding for Similarity Search

The Filing Agent generates a vector embedding of the claim description to enable downstream similarity search against historical claims.

```json
// EmbeddingGenerator: Generate embedding for the claim description
{
  "tool": "EmbeddingGenerator",
  "method": "generateEmbedding",
  "params": {
    "model": "text-embedding-3-small",
    "input": "Rear-end collision at stoplight. Vehicle stationary at red light struck from behind. Rear bumper cracked, trunk dented, tail-light displaced. Other driver admitted fault. Police report filed. No injuries. Minor severity. Estimated repair $2,800.",
    "dimensions": 1536
  }
}
```

**Response:**
```json
{
  "embedding": [0.0123, -0.0456, 0.0789, "...1536 floats total..."],
  "model": "text-embedding-3-small",
  "tokensUsed": 48
}
```

```json
// MongoDB MCP: updateOne — store embedding on the claim document
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00143" },
    "update": {
      "$set": {
        "embedding": [0.0123, -0.0456, 0.0789, "...1536 floats..."],
        "status": "pending_assessment",
        "updatedAt": "2025-03-12T16:46:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

---

### What the Assessment Agent Determines

#### Step 1 — Retrieve the Filed Claim

```json
// MongoDB MCP: findOne on claims collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00143" }
  }
}
```

#### Step 2 — Search for Similar Historical Claims

The Assessment Agent uses the claim's embedding to find past claims with similar circumstances and damage patterns.

```json
// MongoDB MCP: aggregate — $vectorSearch for similar past claims
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      {
        "$vectorSearch": {
          "index": "claims_vector_index",
          "path": "embedding",
          "queryVector": [0.0123, -0.0456, 0.0789, "...1536 floats..."],
          "numCandidates": 100,
          "limit": 5,
          "filter": {
            "status": "closed",
            "type": "collision"
          }
        }
      },
      {
        "$project": {
          "claimId": 1,
          "description": 1,
          "estimatedRepairCost": 1,
          "actualRepairCost": 1,
          "resolution": 1,
          "score": { "$meta": "vectorSearchScore" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "claimId": "CLM-2024-08912",
    "description": "Rear-end collision at intersection. Bumper and trunk damage.",
    "estimatedRepairCost": 2600,
    "actualRepairCost": 2750,
    "resolution": "approved",
    "score": 0.94
  },
  {
    "claimId": "CLM-2024-11204",
    "description": "Rear-end impact in traffic. Bumper replacement needed.",
    "estimatedRepairCost": 3100,
    "actualRepairCost": 2980,
    "resolution": "approved",
    "score": 0.91
  },
  {
    "claimId": "CLM-2024-06337",
    "description": "Low-speed rear collision. Cosmetic bumper damage only.",
    "estimatedRepairCost": 1800,
    "actualRepairCost": 1650,
    "resolution": "approved",
    "score": 0.88
  }
]
```

#### Step 3 — Evaluate and Render Decision

Based on image analysis (minor severity), straightforward liability (other driver at fault and admitted it), police report corroboration, and strong similarity to historically approved claims, the Assessment Agent approves the claim.

```json
// MongoDB MCP: updateOne — record assessment decision
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00143" },
    "update": {
      "$set": {
        "status": "approved",
        "assessment": {
          "decision": "approved",
          "assessedAt": "2025-03-12T17:02:00Z",
          "approvedAmount": 2800,
          "deductibleApplied": 500,
          "payoutAmount": 2300,
          "coverageUsed": "collision",
          "liabilityDetermination": "other_party_at_fault",
          "fraudRiskScore": 0.03,
          "similarClaimsReferenced": ["CLM-2024-08912", "CLM-2024-11204", "CLM-2024-06337"],
          "reasoning": "Clear liability — other driver admitted fault, police report confirms. Damage consistent with low-speed rear-end impact. Repair estimate within expected range based on 3 similar historical claims (avg actual cost $2,460). No fraud indicators. Recommend approval with standard deductible.",
          "requiresManualReview": false
        },
        "updatedAt": "2025-03-12T17:02:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

**Outcome:** Claim approved. Sarah Chen receives **$2,300** ($2,800 − $500 deductible). The insurer may subrogate against the other driver's carrier to recover the payout.

---

---

## Scenario 2: Parking Lot Hit-and-Run

**Type:** Uninsured motorist property damage · No other party identified  
**Customer:** Marcus Williams · **Policy:** POL-2024-55891  
**Damage:** Driver-side door caved in, quarter panel gouged  
**Injuries:** None  
**Estimated Repair:** $6,200 · **Deductible:** $250

---

### Description of the Accident

On April 5, 2025, Marcus Williams returned to his 2023 Ford Escape in the Eastgate Mall parking lot in Charlotte, NC after a two-hour shopping trip. He discovered that the driver-side door was severely dented inward with paint transfer (white paint on his blue vehicle), the rear quarter panel had a deep horizontal gouge, and the side mirror housing was shattered. No note was left. Mall security confirmed their parking lot cameras had been offline for maintenance that day. Marcus filed a police report (Report #CPD-2025-07823) and documented the damage with four photos.

---

### What the Customer Says

> "I came back to my car at Eastgate Mall and found the driver-side door completely smashed in. There's white paint all over it so someone definitely hit me, but there's no note, nothing. I talked to mall security and they said their cameras were down today — just my luck. I filed a police report but the officer said they probably can't find who did it. My policy is POL-2024-55891. The door barely opens now; I can only get in from the passenger side."

---

### What the Filing Agent Does

#### Step 1 — Validate the Policy

```json
// MongoDB MCP: findOne on policies collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "policies",
    "filter": { "policyNumber": "POL-2024-55891" }
  }
}
```

**Response:**
```json
{
  "policyNumber": "POL-2024-55891",
  "holder": "Marcus Williams",
  "status": "active",
  "vehicle": {
    "year": 2023,
    "make": "Ford",
    "model": "Escape",
    "vin": "1FMCU9J94NUA78901"
  },
  "coverages": {
    "collision": { "deductible": 500, "limit": 50000 },
    "comprehensive": { "deductible": 250, "limit": 50000 },
    "liability": { "bodilyInjury": 100000, "propertyDamage": 50000 },
    "uninsuredMotorist": { "deductible": 250, "limit": 50000 }
  },
  "premiumStatus": "current"
}
```

The Filing Agent identifies that because the at-fault party is unknown, **uninsured motorist property damage (UMPD)** coverage applies with a $250 deductible.

#### Step 2 — Analyze Uploaded Damage Photos

```json
// ImageAnalyzer: Analyze damage photo 1 of 4
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-driver-door-01>",
    "vehicleContext": {
      "year": 2023,
      "make": "Ford",
      "model": "Escape"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "driver_side_door",
      "damageType": "dent_with_paint_transfer",
      "severity": "severe",
      "confidenceScore": 0.95,
      "boundingBox": { "x": 80, "y": 200, "w": 520, "h": 300 },
      "notes": "Deep intrusion dent with white paint transfer. Door skin buckled."
    }
  ],
  "overallSeverity": "moderate_to_severe",
  "estimatedRepairRange": { "low": 3800, "high": 5200 }
}
```

```json
// ImageAnalyzer: Analyze damage photo 2 of 4
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-quarter-panel-02>",
    "vehicleContext": {
      "year": 2023,
      "make": "Ford",
      "model": "Escape"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "rear_quarter_panel_left",
      "damageType": "gouge",
      "severity": "moderate",
      "confidenceScore": 0.91,
      "boundingBox": { "x": 300, "y": 250, "w": 400, "h": 80 }
    },
    {
      "part": "side_mirror_left",
      "damageType": "shattered",
      "severity": "severe",
      "confidenceScore": 0.96,
      "boundingBox": { "x": 10, "y": 100, "w": 120, "h": 110 }
    }
  ],
  "overallSeverity": "moderate",
  "estimatedRepairRange": { "low": 1200, "high": 2000 }
}
```

#### Step 3 — Create the Claim Record

```json
// MongoDB MCP: insertOne into claims collection
{
  "tool": "mongodb_mcp",
  "method": "insertOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "document": {
      "claimId": "CLM-2025-00287",
      "policyNumber": "POL-2024-55891",
      "claimant": "Marcus Williams",
      "dateOfLoss": "2025-04-05T12:00:00Z",
      "dateReported": "2025-04-05T14:20:00Z",
      "status": "filed",
      "type": "uninsured_motorist",
      "description": "Hit-and-run in parking lot. Vehicle was parked and unoccupied at Eastgate Mall. Unknown vehicle struck driver side, leaving white paint transfer. No witnesses, security cameras offline. Police report filed.",
      "location": {
        "name": "Eastgate Mall Parking Lot",
        "city": "Charlotte",
        "state": "NC"
      },
      "policeReportNumber": "CPD-2025-07823",
      "otherParty": {
        "identified": false,
        "hitAndRun": true,
        "paintTransfer": "white"
      },
      "injuries": {
        "reported": false
      },
      "damages": [
        { "part": "driver_side_door", "type": "dent_with_paint_transfer", "severity": "severe" },
        { "part": "rear_quarter_panel_left", "type": "gouge", "severity": "moderate" },
        { "part": "side_mirror_left", "type": "shattered", "severity": "severe" }
      ],
      "estimatedRepairCost": 6200,
      "deductible": 250,
      "coverageApplied": "uninsured_motorist",
      "imageAnalysisResults": [
        { "photoId": "img-010", "overallSeverity": "moderate_to_severe", "confidence": 0.95 },
        { "photoId": "img-011", "overallSeverity": "moderate", "confidence": 0.91 }
      ],
      "createdAt": "2025-04-05T14:20:00Z",
      "updatedAt": "2025-04-05T14:20:00Z"
    }
  }
}
```

**Response:**
```json
{
  "acknowledged": true,
  "insertedId": "65f2b3c4d5e6f7a8b9c0d1e2"
}
```

#### Step 4 — Generate Claim Embedding

```json
// EmbeddingGenerator: Generate embedding for the claim description
{
  "tool": "EmbeddingGenerator",
  "method": "generateEmbedding",
  "params": {
    "model": "text-embedding-3-small",
    "input": "Hit-and-run in parking lot. Vehicle parked and unoccupied. Unknown vehicle struck driver side leaving white paint transfer. Driver door severely dented, quarter panel gouged, mirror shattered. No witnesses, security cameras offline. Police report filed. No injuries. Moderate to severe damage. Estimated repair $6,200.",
    "dimensions": 1536
  }
}
```

**Response:**
```json
{
  "embedding": [0.0234, -0.0567, 0.0891, "...1536 floats total..."],
  "model": "text-embedding-3-small",
  "tokensUsed": 62
}
```

```json
// MongoDB MCP: updateOne — store embedding on the claim document
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00287" },
    "update": {
      "$set": {
        "embedding": [0.0234, -0.0567, 0.0891, "...1536 floats..."],
        "status": "pending_assessment",
        "updatedAt": "2025-04-05T14:21:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

---

### What the Assessment Agent Determines

#### Step 1 — Retrieve the Filed Claim

```json
// MongoDB MCP: findOne on claims collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00287" }
  }
}
```

#### Step 2 — Search for Similar Historical Claims

```json
// MongoDB MCP: aggregate — $vectorSearch for similar past claims
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      {
        "$vectorSearch": {
          "index": "claims_vector_index",
          "path": "embedding",
          "queryVector": [0.0234, -0.0567, 0.0891, "...1536 floats..."],
          "numCandidates": 100,
          "limit": 5,
          "filter": {
            "status": "closed",
            "type": "uninsured_motorist"
          }
        }
      },
      {
        "$project": {
          "claimId": 1,
          "description": 1,
          "estimatedRepairCost": 1,
          "actualRepairCost": 1,
          "resolution": 1,
          "fraudRiskScore": 1,
          "score": { "$meta": "vectorSearchScore" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "claimId": "CLM-2024-15782",
    "description": "Parking lot hit-and-run. Door and fender damage with paint transfer.",
    "estimatedRepairCost": 5800,
    "actualRepairCost": 6100,
    "resolution": "approved",
    "fraudRiskScore": 0.05,
    "score": 0.92
  },
  {
    "claimId": "CLM-2024-19034",
    "description": "Hit-and-run while parked at grocery store. Side panel damage.",
    "estimatedRepairCost": 4200,
    "actualRepairCost": 4450,
    "resolution": "approved",
    "fraudRiskScore": 0.08,
    "score": 0.89
  },
  {
    "claimId": "CLM-2024-22198",
    "description": "Parking structure hit-and-run. Door replacement needed.",
    "estimatedRepairCost": 7100,
    "actualRepairCost": 6800,
    "resolution": "approved",
    "fraudRiskScore": 0.12,
    "score": 0.86
  }
]
```

#### Step 3 — Fraud Pattern Check

The Assessment Agent notes that parking lot hit-and-runs carry a slightly elevated fraud risk. It cross-references claim history for the policyholder.

```json
// MongoDB MCP: aggregate — check claimant history
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      { "$match": { "policyNumber": "POL-2024-55891" } },
      { "$group": {
          "_id": "$policyNumber",
          "totalClaims": { "$sum": 1 },
          "hitAndRunClaims": { "$sum": { "$cond": [{ "$eq": ["$otherParty.hitAndRun", true] }, 1, 0] } },
          "totalPaidOut": { "$sum": "$assessment.payoutAmount" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "_id": "POL-2024-55891",
    "totalClaims": 1,
    "hitAndRunClaims": 1,
    "totalPaidOut": 0
  }
]
```

No prior claims — this is Marcus's first claim. Fraud risk is low.

#### Step 4 — Evaluate and Render Decision

```json
// MongoDB MCP: updateOne — record assessment decision
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00287" },
    "update": {
      "$set": {
        "status": "approved",
        "assessment": {
          "decision": "approved",
          "assessedAt": "2025-04-05T15:10:00Z",
          "approvedAmount": 6200,
          "deductibleApplied": 250,
          "payoutAmount": 5950,
          "coverageUsed": "uninsured_motorist",
          "liabilityDetermination": "unknown_party_at_fault",
          "fraudRiskScore": 0.07,
          "similarClaimsReferenced": ["CLM-2024-15782", "CLM-2024-19034", "CLM-2024-22198"],
          "reasoning": "Damage pattern consistent with parking lot side-swipe. White paint transfer corroborates contact with another vehicle. Police report confirms hit-and-run classification. No prior claims on this policy; low fraud risk. Repair estimate aligns with similar historical claims (avg actual cost $5,783). Covered under uninsured motorist property damage. Recommend approval.",
          "requiresManualReview": false
        },
        "updatedAt": "2025-04-05T15:10:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

**Outcome:** Claim approved. Marcus Williams receives **$5,950** ($6,200 − $250 deductible). No subrogation possible without an identified at-fault party.

---

---

## Scenario 3: Multi-Vehicle Highway Accident

**Type:** Complex collision · Multiple parties · Injuries reported  
**Customer:** Jennifer Park · **Policy:** POL-2024-91204  
**Damage:** Front-end severe — radiator, hood, both headlights destroyed, airbags deployed  
**Injuries:** Minor whiplash  
**Estimated Repair:** $18,500 · **Deductible:** $1,000  
**Flags:** Requires investigation

---

### Description of the Accident

On May 18, 2025 at approximately 5:45 PM during rush hour, Jennifer Park was driving her 2021 Subaru Outback westbound on I-90 near mile marker 42 outside Chicago, IL. A pickup truck three cars ahead braked suddenly due to debris in the road. A chain-reaction collision ensued: the car directly in front of Jennifer (a black BMW 5 Series) braked hard and stopped, and Jennifer braked but could not stop in time, rear-ending the BMW at approximately 30 mph. Immediately after, a delivery van behind Jennifer rear-ended her Subaru, pushing it further into the BMW. Jennifer's front airbags deployed. She experienced neck pain and was evaluated by paramedics on scene, diagnosed with minor whiplash, and declined ambulance transport. Three vehicles total were involved. State police responded and created a multi-vehicle accident report (Report #ISP-2025-MV-0892). Liability is disputed — Jennifer may share partial fault for following too closely, but the van driver behind her contributed to the severity.

---

### What the Customer Says

> "It was a nightmare. Traffic was heavy on I-90 and suddenly everyone slammed their brakes. I hit the car in front of me — a black BMW — and then a van hit me from behind which pushed me into the BMW again. My airbags went off, the whole front of my car is destroyed. The hood is buckled, my headlights are gone, there's fluid leaking. My neck really hurts — the paramedics said it's probably whiplash. The state police made a big report because there were three cars involved. My policy number is POL-2024-91204. I'm not sure who's at fault here — there was debris in the road that started the whole thing."

---

### What the Filing Agent Does

#### Step 1 — Validate the Policy

```json
// MongoDB MCP: findOne on policies collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "policies",
    "filter": { "policyNumber": "POL-2024-91204" }
  }
}
```

**Response:**
```json
{
  "policyNumber": "POL-2024-91204",
  "holder": "Jennifer Park",
  "status": "active",
  "vehicle": {
    "year": 2021,
    "make": "Subaru",
    "model": "Outback",
    "vin": "4S4BTACC3M3234567"
  },
  "coverages": {
    "collision": { "deductible": 1000, "limit": 75000 },
    "comprehensive": { "deductible": 500, "limit": 75000 },
    "liability": { "bodilyInjury": 250000, "propertyDamage": 100000 },
    "uninsuredMotorist": { "deductible": 500, "limit": 100000 },
    "medicalPayments": { "limit": 10000 },
    "rentalReimbursement": { "dailyLimit": 50, "maxDays": 30 }
  },
  "premiumStatus": "current"
}
```

#### Step 2 — Analyze Uploaded Damage Photos

```json
// ImageAnalyzer: Analyze damage photo 1 of 5
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-front-end-01>",
    "vehicleContext": {
      "year": 2021,
      "make": "Subaru",
      "model": "Outback"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "hood",
      "damageType": "buckled",
      "severity": "severe",
      "confidenceScore": 0.97,
      "boundingBox": { "x": 50, "y": 30, "w": 600, "h": 250 }
    },
    {
      "part": "front_bumper",
      "damageType": "crushed",
      "severity": "severe",
      "confidenceScore": 0.98,
      "boundingBox": { "x": 30, "y": 300, "w": 640, "h": 120 }
    },
    {
      "part": "headlight_assembly_both",
      "damageType": "destroyed",
      "severity": "severe",
      "confidenceScore": 0.96,
      "boundingBox": { "x": 10, "y": 200, "w": 680, "h": 100 }
    },
    {
      "part": "radiator",
      "damageType": "punctured",
      "severity": "severe",
      "confidenceScore": 0.93,
      "notes": "Coolant leak visible in image"
    }
  ],
  "overallSeverity": "severe",
  "estimatedRepairRange": { "low": 14000, "high": 22000 },
  "airbagDeployment": true,
  "totalLossCandidate": false
}
```

```json
// ImageAnalyzer: Analyze damage photo 2 of 5 — rear damage from van impact
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-rear-damage-02>",
    "vehicleContext": {
      "year": 2021,
      "make": "Subaru",
      "model": "Outback"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "rear_bumper",
      "damageType": "crushed",
      "severity": "moderate",
      "confidenceScore": 0.90,
      "boundingBox": { "x": 40, "y": 320, "w": 600, "h": 100 }
    },
    {
      "part": "liftgate",
      "damageType": "dent",
      "severity": "minor",
      "confidenceScore": 0.85,
      "boundingBox": { "x": 100, "y": 150, "w": 500, "h": 170 }
    }
  ],
  "overallSeverity": "moderate",
  "estimatedRepairRange": { "low": 2500, "high": 4000 }
}
```

#### Step 3 — Create the Claim Record

```json
// MongoDB MCP: insertOne into claims collection
{
  "tool": "mongodb_mcp",
  "method": "insertOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "document": {
      "claimId": "CLM-2025-00412",
      "policyNumber": "POL-2024-91204",
      "claimant": "Jennifer Park",
      "dateOfLoss": "2025-05-18T17:45:00Z",
      "dateReported": "2025-05-18T20:30:00Z",
      "status": "filed",
      "type": "collision",
      "complexity": "high",
      "description": "Multi-vehicle chain-reaction collision on I-90 during rush hour. Debris in road caused lead vehicle to brake suddenly. Claimant rear-ended BMW in front; delivery van rear-ended claimant from behind. Front-end severely damaged — hood buckled, bumper crushed, headlights destroyed, radiator punctured, airbags deployed. Also rear damage from van impact. Three vehicles involved, disputed liability.",
      "location": {
        "highway": "I-90 Westbound",
        "mileMarker": 42,
        "city": "Chicago",
        "state": "IL"
      },
      "policeReportNumber": "ISP-2025-MV-0892",
      "otherParties": [
        {
          "vehicle": "BMW 5 Series (black)",
          "position": "front",
          "identified": true,
          "insuranceExchanged": true
        },
        {
          "vehicle": "Delivery Van (white)",
          "position": "rear",
          "identified": true,
          "insuranceExchanged": true
        }
      ],
      "injuries": {
        "reported": true,
        "claimantInjuries": [
          {
            "type": "whiplash",
            "severity": "minor",
            "treatmentSought": "paramedic_evaluation_on_scene",
            "hospitalTransport": false
          }
        ]
      },
      "damages": [
        { "part": "hood", "type": "buckled", "severity": "severe" },
        { "part": "front_bumper", "type": "crushed", "severity": "severe" },
        { "part": "headlight_assembly_both", "type": "destroyed", "severity": "severe" },
        { "part": "radiator", "type": "punctured", "severity": "severe" },
        { "part": "rear_bumper", "type": "crushed", "severity": "moderate" },
        { "part": "liftgate", "type": "dent", "severity": "minor" }
      ],
      "airbagDeployment": true,
      "estimatedRepairCost": 18500,
      "deductible": 1000,
      "coverageApplied": "collision",
      "additionalCoverages": ["medicalPayments", "rentalReimbursement"],
      "imageAnalysisResults": [
        { "photoId": "img-020", "overallSeverity": "severe", "confidence": 0.97 },
        { "photoId": "img-021", "overallSeverity": "moderate", "confidence": 0.90 }
      ],
      "flags": ["multi_vehicle", "injuries_reported", "airbag_deployment", "disputed_liability"],
      "createdAt": "2025-05-18T20:30:00Z",
      "updatedAt": "2025-05-18T20:30:00Z"
    }
  }
}
```

**Response:**
```json
{
  "acknowledged": true,
  "insertedId": "65f3c4d5e6f7a8b9c0d1e2f3"
}
```

#### Step 4 — Generate Claim Embedding

```json
// EmbeddingGenerator: Generate embedding for the claim description
{
  "tool": "EmbeddingGenerator",
  "method": "generateEmbedding",
  "params": {
    "model": "text-embedding-3-small",
    "input": "Multi-vehicle chain-reaction highway collision during rush hour. Debris caused sudden braking. Rear-ended car in front, then struck from behind by delivery van. Front-end severe damage, hood buckled, bumper crushed, headlights destroyed, radiator punctured, airbags deployed. Rear bumper crushed. Whiplash injury. Three vehicles, disputed liability. Estimated repair $18,500.",
    "dimensions": 1536
  }
}
```

**Response:**
```json
{
  "embedding": [0.0345, -0.0678, 0.0912, "...1536 floats total..."],
  "model": "text-embedding-3-small",
  "tokensUsed": 74
}
```

```json
// MongoDB MCP: updateOne — store embedding on the claim document
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00412" },
    "update": {
      "$set": {
        "embedding": [0.0345, -0.0678, 0.0912, "...1536 floats..."],
        "status": "pending_assessment",
        "updatedAt": "2025-05-18T20:31:00Z"
      }
    }
  }
}
```

---

### What the Assessment Agent Determines

#### Step 1 — Retrieve the Filed Claim

```json
// MongoDB MCP: findOne on claims collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00412" }
  }
}
```

The Assessment Agent flags this claim as **high complexity** based on: multiple parties, injuries, airbag deployment, and disputed liability.

#### Step 2 — Search for Similar Historical Claims

```json
// MongoDB MCP: aggregate — $vectorSearch for similar past claims
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      {
        "$vectorSearch": {
          "index": "claims_vector_index",
          "path": "embedding",
          "queryVector": [0.0345, -0.0678, 0.0912, "...1536 floats..."],
          "numCandidates": 150,
          "limit": 5,
          "filter": {
            "status": "closed",
            "complexity": "high"
          }
        }
      },
      {
        "$project": {
          "claimId": 1,
          "description": 1,
          "estimatedRepairCost": 1,
          "actualRepairCost": 1,
          "resolution": 1,
          "liabilityDetermination": 1,
          "score": { "$meta": "vectorSearchScore" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "claimId": "CLM-2024-31045",
    "description": "Multi-vehicle pile-up on highway. Chain reaction. Front and rear damage, airbags deployed.",
    "estimatedRepairCost": 21000,
    "actualRepairCost": 19800,
    "resolution": "approved_partial_liability",
    "liabilityDetermination": "shared_40_60",
    "score": 0.91
  },
  {
    "claimId": "CLM-2024-28891",
    "description": "Three-car collision on interstate. Braking chain reaction. Severe front damage, minor whiplash.",
    "estimatedRepairCost": 16500,
    "actualRepairCost": 17200,
    "resolution": "approved_with_investigation",
    "liabilityDetermination": "shared_30_70",
    "score": 0.88
  },
  {
    "claimId": "CLM-2024-35220",
    "description": "Highway rear-end chain collision. Airbags deployed. Multiple parties, injuries.",
    "estimatedRepairCost": 24000,
    "actualRepairCost": 22100,
    "resolution": "approved_partial_liability",
    "liabilityDetermination": "shared_50_50",
    "score": 0.85
  }
]
```

#### Step 3 — Medical Claim Cross-Reference

```json
// MongoDB MCP: findOne — check for medical payment sub-claim
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "medical_claims",
    "filter": {
      "parentClaimId": "CLM-2025-00412",
      "claimant": "Jennifer Park"
    }
  }
}
```

**Response:**
```json
null
```

No medical sub-claim filed yet. The Assessment Agent notes that Jennifer may submit medical expenses later under her MedPay coverage ($10,000 limit).

#### Step 4 — Evaluate and Render Decision

Given the complexity — multiple parties, disputed liability, injuries, and airbag deployment — the Assessment Agent escalates to manual review but provides its preliminary assessment.

```json
// MongoDB MCP: updateOne — record assessment decision
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00412" },
    "update": {
      "$set": {
        "status": "under_investigation",
        "assessment": {
          "decision": "pending_manual_review",
          "assessedAt": "2025-05-18T21:15:00Z",
          "preliminaryApprovedAmount": 18500,
          "deductibleApplied": 1000,
          "preliminaryPayoutAmount": 17500,
          "coverageUsed": "collision",
          "liabilityDetermination": "shared_liability_pending_investigation",
          "preliminaryLiabilitySplit": {
            "claimant": 30,
            "bmwDriver": 0,
            "vanDriver": 70,
            "reasoning": "Claimant may bear partial responsibility for following distance. Van driver bears primary responsibility for rear-end impact that increased severity. Road debris is a contributing factor that may reduce individual liability."
          },
          "fraudRiskScore": 0.04,
          "similarClaimsReferenced": ["CLM-2024-31045", "CLM-2024-28891", "CLM-2024-35220"],
          "reasoning": "High-complexity multi-vehicle collision with injuries and airbag deployment. Damage estimates are consistent with similar historical claims. Liability is disputed and requires investigation — preliminary split suggests 30/70 claimant/van driver. Whiplash injury may generate additional medical claims. Recommend assignment to senior adjuster for manual review and liability negotiation with other carriers.",
          "requiresManualReview": true,
          "manualReviewReasons": [
            "multi_vehicle_accident",
            "disputed_liability",
            "injuries_reported",
            "airbag_deployment",
            "potential_subrogation_multiple_parties"
          ],
          "additionalCoverageNotes": {
            "medicalPayments": "Claimant has $10,000 MedPay. Whiplash treatment costs may be submitted separately.",
            "rentalReimbursement": "Eligible for rental car up to $50/day for 30 days during repair period."
          }
        },
        "updatedAt": "2025-05-18T21:15:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

**Outcome:** Claim routed to **manual review / senior adjuster**. Preliminary payout estimate is **$17,500** ($18,500 − $1,000 deductible), subject to liability investigation. Jennifer is eligible for rental car reimbursement ($50/day, up to 30 days) and may file a separate MedPay claim for whiplash treatment up to $10,000. Liability negotiation with the van driver's insurer will follow.

---

---

## Scenario 4: Single Vehicle — Weather Related

**Type:** Single vehicle · Ice/weather · Comprehensive coverage  
**Customer:** David Kowalski · **Policy:** POL-2024-33567  
**Damage:** Right-side body damage, broken passenger mirror, scraped wheel  
**Injuries:** None  
**Estimated Repair:** $4,100 · **Deductible:** $500

---

### Description of the Accident

On February 2, 2025 at approximately 7:15 AM, David Kowalski was driving his 2020 Honda CR-V eastbound on County Road 9 near Minneapolis, MN. A freezing rain event overnight had left black ice on the roadway. As David crested a small hill, his vehicle lost traction and skidded sideways into a metal guardrail on the right shoulder. The impact scraped the entire right side of the vehicle, caved in the passenger-side mirror, and curbed the front-right wheel. David regained control and was able to drive the vehicle to a nearby gas station. No other vehicles were involved. David did not file a police report (single vehicle, no injuries) but did take photos and checked the weather service advisory confirming a freezing rain warning for the area that morning.

---

### What the Customer Says

> "I hit a patch of black ice on County Road 9 this morning and slid right into the guardrail. The whole right side of my car is scraped up, the passenger mirror is hanging off, and I think I bent the wheel too. Nobody else was involved, it was just the ice. I didn't file a police report since it was just me and the guardrail, but I have pictures and there was definitely a weather advisory for freezing rain. My policy number is POL-2024-33567."

---

### What the Filing Agent Does

#### Step 1 — Validate the Policy

```json
// MongoDB MCP: findOne on policies collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "policies",
    "filter": { "policyNumber": "POL-2024-33567" }
  }
}
```

**Response:**
```json
{
  "policyNumber": "POL-2024-33567",
  "holder": "David Kowalski",
  "status": "active",
  "vehicle": {
    "year": 2020,
    "make": "Honda",
    "model": "CR-V",
    "vin": "2HKRW2H52LH345678"
  },
  "coverages": {
    "collision": { "deductible": 500, "limit": 50000 },
    "comprehensive": { "deductible": 500, "limit": 50000 },
    "liability": { "bodilyInjury": 100000, "propertyDamage": 50000 },
    "uninsuredMotorist": { "deductible": 250, "limit": 50000 }
  },
  "premiumStatus": "current"
}
```

The Filing Agent determines that because the loss was caused by weather conditions (ice), **collision coverage** applies (single-vehicle collision with a fixed object). Note: Some jurisdictions may classify weather-related single-vehicle losses under comprehensive; the Filing Agent applies collision here since the vehicle struck a guardrail.

#### Step 2 — Analyze Uploaded Damage Photos

```json
// ImageAnalyzer: Analyze damage photo 1 of 3
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-right-side-01>",
    "vehicleContext": {
      "year": 2020,
      "make": "Honda",
      "model": "CR-V"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "right_front_fender",
      "damageType": "scrape_and_dent",
      "severity": "moderate",
      "confidenceScore": 0.93,
      "boundingBox": { "x": 50, "y": 180, "w": 300, "h": 200 }
    },
    {
      "part": "right_front_door",
      "damageType": "scrape",
      "severity": "moderate",
      "confidenceScore": 0.91,
      "boundingBox": { "x": 350, "y": 180, "w": 280, "h": 200 }
    },
    {
      "part": "right_rear_door",
      "damageType": "scrape",
      "severity": "minor",
      "confidenceScore": 0.88,
      "boundingBox": { "x": 630, "y": 200, "w": 200, "h": 180 }
    }
  ],
  "overallSeverity": "moderate",
  "estimatedRepairRange": { "low": 2800, "high": 4200 }
}
```

```json
// ImageAnalyzer: Analyze damage photo 2 of 3 — mirror and wheel
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-mirror-wheel-02>",
    "vehicleContext": {
      "year": 2020,
      "make": "Honda",
      "model": "CR-V"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "side_mirror_right",
      "damageType": "broken_housing",
      "severity": "severe",
      "confidenceScore": 0.94,
      "boundingBox": { "x": 20, "y": 60, "w": 140, "h": 130 }
    },
    {
      "part": "wheel_front_right",
      "damageType": "curb_damage",
      "severity": "moderate",
      "confidenceScore": 0.86,
      "boundingBox": { "x": 200, "y": 300, "w": 200, "h": 200 }
    }
  ],
  "overallSeverity": "moderate",
  "estimatedRepairRange": { "low": 600, "high": 1100 }
}
```

#### Step 3 — Create the Claim Record

```json
// MongoDB MCP: insertOne into claims collection
{
  "tool": "mongodb_mcp",
  "method": "insertOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "document": {
      "claimId": "CLM-2025-00098",
      "policyNumber": "POL-2024-33567",
      "claimant": "David Kowalski",
      "dateOfLoss": "2025-02-02T07:15:00Z",
      "dateReported": "2025-02-02T09:00:00Z",
      "status": "filed",
      "type": "collision",
      "subtype": "single_vehicle_weather",
      "description": "Single-vehicle weather-related accident. Vehicle skidded on black ice on County Road 9 and struck metal guardrail on right shoulder. Right side scraped along full length, passenger mirror broken, front-right wheel curbed. No other vehicles involved. Weather advisory confirmed freezing rain conditions.",
      "location": {
        "road": "County Road 9",
        "city": "Minneapolis",
        "state": "MN"
      },
      "policeReportNumber": null,
      "weatherConditions": {
        "condition": "freezing_rain",
        "roadCondition": "black_ice",
        "advisoryConfirmed": true
      },
      "otherParty": {
        "identified": false,
        "singleVehicle": true
      },
      "injuries": {
        "reported": false
      },
      "damages": [
        { "part": "right_front_fender", "type": "scrape_and_dent", "severity": "moderate" },
        { "part": "right_front_door", "type": "scrape", "severity": "moderate" },
        { "part": "right_rear_door", "type": "scrape", "severity": "minor" },
        { "part": "side_mirror_right", "type": "broken_housing", "severity": "severe" },
        { "part": "wheel_front_right", "type": "curb_damage", "severity": "moderate" }
      ],
      "estimatedRepairCost": 4100,
      "deductible": 500,
      "coverageApplied": "collision",
      "imageAnalysisResults": [
        { "photoId": "img-030", "overallSeverity": "moderate", "confidence": 0.93 },
        { "photoId": "img-031", "overallSeverity": "moderate", "confidence": 0.94 }
      ],
      "createdAt": "2025-02-02T09:00:00Z",
      "updatedAt": "2025-02-02T09:00:00Z"
    }
  }
}
```

**Response:**
```json
{
  "acknowledged": true,
  "insertedId": "65f4d5e6f7a8b9c0d1e2f3a4"
}
```

#### Step 4 — Generate Claim Embedding

```json
// EmbeddingGenerator: Generate embedding for the claim description
{
  "tool": "EmbeddingGenerator",
  "method": "generateEmbedding",
  "params": {
    "model": "text-embedding-3-small",
    "input": "Single-vehicle weather-related accident. Skidded on black ice, struck guardrail. Right side scraped, passenger mirror broken, wheel curbed. No other vehicles. Freezing rain advisory confirmed. No injuries. Moderate damage. Estimated repair $4,100.",
    "dimensions": 1536
  }
}
```

**Response:**
```json
{
  "embedding": [0.0456, -0.0789, 0.1012, "...1536 floats total..."],
  "model": "text-embedding-3-small",
  "tokensUsed": 52
}
```

```json
// MongoDB MCP: updateOne — store embedding on the claim document
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00098" },
    "update": {
      "$set": {
        "embedding": [0.0456, -0.0789, 0.1012, "...1536 floats..."],
        "status": "pending_assessment",
        "updatedAt": "2025-02-02T09:01:00Z"
      }
    }
  }
}
```

---

### What the Assessment Agent Determines

#### Step 1 — Retrieve the Filed Claim

```json
// MongoDB MCP: findOne on claims collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00098" }
  }
}
```

#### Step 2 — Verify Weather Conditions

The Assessment Agent corroborates the claimant's weather statement against historical weather data.

```json
// MongoDB MCP: findOne — weather records
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "weather_records",
    "filter": {
      "date": "2025-02-02",
      "region": "Minneapolis-MN",
      "advisoryType": "freezing_rain"
    }
  }
}
```

**Response:**
```json
{
  "date": "2025-02-02",
  "region": "Minneapolis-MN",
  "advisoryType": "freezing_rain",
  "issuedAt": "2025-02-01T22:00:00Z",
  "expiresAt": "2025-02-02T14:00:00Z",
  "conditions": "Freezing rain expected overnight through midday. Black ice likely on untreated surfaces.",
  "source": "NWS"
}
```

Weather advisory confirmed. The accident occurred within the advisory window.

#### Step 3 — Search for Similar Historical Claims

```json
// MongoDB MCP: aggregate — $vectorSearch for similar past claims
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      {
        "$vectorSearch": {
          "index": "claims_vector_index",
          "path": "embedding",
          "queryVector": [0.0456, -0.0789, 0.1012, "...1536 floats..."],
          "numCandidates": 100,
          "limit": 5,
          "filter": {
            "status": "closed",
            "subtype": "single_vehicle_weather"
          }
        }
      },
      {
        "$project": {
          "claimId": 1,
          "description": 1,
          "estimatedRepairCost": 1,
          "actualRepairCost": 1,
          "resolution": 1,
          "score": { "$meta": "vectorSearchScore" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "claimId": "CLM-2024-02145",
    "description": "Skidded on ice into guardrail. Right side damage, mirror broken.",
    "estimatedRepairCost": 3900,
    "actualRepairCost": 4050,
    "resolution": "approved",
    "score": 0.95
  },
  {
    "claimId": "CLM-2024-02890",
    "description": "Black ice single-vehicle slide into highway barrier. Side scrapes and wheel damage.",
    "estimatedRepairCost": 4500,
    "actualRepairCost": 4200,
    "resolution": "approved",
    "score": 0.93
  },
  {
    "claimId": "CLM-2024-01567",
    "description": "Freezing rain caused vehicle to slide off road into ditch. Side panel and mirror damage.",
    "estimatedRepairCost": 3200,
    "actualRepairCost": 3400,
    "resolution": "approved",
    "score": 0.90
  }
]
```

#### Step 4 — Evaluate and Render Decision

```json
// MongoDB MCP: updateOne — record assessment decision
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00098" },
    "update": {
      "$set": {
        "status": "approved",
        "assessment": {
          "decision": "approved",
          "assessedAt": "2025-02-02T10:30:00Z",
          "approvedAmount": 4100,
          "deductibleApplied": 500,
          "payoutAmount": 3600,
          "coverageUsed": "collision",
          "liabilityDetermination": "single_vehicle_weather_no_fault",
          "weatherVerified": true,
          "fraudRiskScore": 0.02,
          "similarClaimsReferenced": ["CLM-2024-02145", "CLM-2024-02890", "CLM-2024-01567"],
          "reasoning": "Single-vehicle weather-related loss confirmed. NWS freezing rain advisory active at time of accident. Damage pattern consistent with lateral guardrail impact — continuous scrape along right side with mirror and wheel damage. No police report, but not unusual for single-vehicle no-injury incidents. Repair estimate within expected range based on 3 similar historical claims (avg actual cost $3,883). No fraud indicators. Recommend approval.",
          "requiresManualReview": false,
          "note": "No police report filed. Absence acceptable for single-vehicle, no-injury weather incidents per company policy."
        },
        "updatedAt": "2025-02-02T10:30:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

**Outcome:** Claim approved. David Kowalski receives **$3,600** ($4,100 − $500 deductible). No subrogation — weather event, no at-fault party.

---

---

## Scenario 5: Total Loss — Intersection T-Bone

**Type:** Severe collision · Vehicle totaled · Payout calculation · Rental coverage  
**Customer:** Aisha Thompson · **Policy:** POL-2024-62718  
**Damage:** Passenger-side impact, B-pillar bent, structural frame damage, side airbags deployed  
**Injuries:** Minor bruising from seatbelt  
**Vehicle Value:** $22,000 · **Deductible:** $1,000

---

### Description of the Accident

On June 10, 2025 at approximately 2:30 PM, Aisha Thompson was driving her 2021 Hyundai Tucson through the intersection of Oak Street and Riverside Boulevard in Denver, CO. She had a green light and was proceeding straight when a red Dodge Ram pickup ran the red light from the cross street and T-boned her vehicle on the passenger side at approximately 40 mph. The impact was devastating: the passenger-side doors were caved in to the center console, the B-pillar was bent, and the structural frame was visibly deformed. Side curtain and side-impact airbags deployed. Aisha was wearing her seatbelt and sustained minor bruising across her chest and shoulder from the restraint. The pickup driver was cited by Denver PD for running a red light (Report #DPD-2025-14209). Two witnesses corroborated that Aisha had the green light. The vehicle was towed from the scene and is not drivable. A body shop preliminary inspection concluded the repair cost would exceed the vehicle's fair market value, recommending a total loss declaration.

---

### What the Customer Says

> "Someone ran a red light and slammed into my car on the passenger side. It happened so fast — I had the green, I was just going straight, and then BAM, this big pickup truck hit me. The whole passenger side is caved in. My airbags went off, there's glass everywhere. The police came and gave the other driver a ticket for running the red, and two people who saw it happen gave statements. My car got towed — it's undrivable. The tow yard guy said it's probably totaled. I have some bruising from the seatbelt but otherwise I'm okay. My policy is POL-2024-62718. I need a rental car — I rely on my car to get to work."

---

### What the Filing Agent Does

#### Step 1 — Validate the Policy

```json
// MongoDB MCP: findOne on policies collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "policies",
    "filter": { "policyNumber": "POL-2024-62718" }
  }
}
```

**Response:**
```json
{
  "policyNumber": "POL-2024-62718",
  "holder": "Aisha Thompson",
  "status": "active",
  "vehicle": {
    "year": 2021,
    "make": "Hyundai",
    "model": "Tucson",
    "vin": "5NMJF3AE0MH456789"
  },
  "coverages": {
    "collision": { "deductible": 1000, "limit": 50000 },
    "comprehensive": { "deductible": 500, "limit": 50000 },
    "liability": { "bodilyInjury": 100000, "propertyDamage": 50000 },
    "uninsuredMotorist": { "deductible": 250, "limit": 50000 },
    "medicalPayments": { "limit": 5000 },
    "rentalReimbursement": { "dailyLimit": 45, "maxDays": 30 }
  },
  "premiumStatus": "current"
}
```

#### Step 2 — Analyze Uploaded Damage Photos

```json
// ImageAnalyzer: Analyze damage photo 1 of 6
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-passenger-side-01>",
    "vehicleContext": {
      "year": 2021,
      "make": "Hyundai",
      "model": "Tucson"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "passenger_front_door",
      "damageType": "caved_in",
      "severity": "catastrophic",
      "confidenceScore": 0.99,
      "boundingBox": { "x": 100, "y": 100, "w": 300, "h": 350 }
    },
    {
      "part": "passenger_rear_door",
      "damageType": "caved_in",
      "severity": "catastrophic",
      "confidenceScore": 0.98,
      "boundingBox": { "x": 400, "y": 110, "w": 280, "h": 340 }
    },
    {
      "part": "b_pillar",
      "damageType": "bent_structural",
      "severity": "catastrophic",
      "confidenceScore": 0.97,
      "boundingBox": { "x": 350, "y": 50, "w": 60, "h": 400 }
    },
    {
      "part": "rocker_panel_right",
      "damageType": "crushed",
      "severity": "severe",
      "confidenceScore": 0.95,
      "boundingBox": { "x": 80, "y": 420, "w": 550, "h": 60 }
    }
  ],
  "overallSeverity": "catastrophic",
  "estimatedRepairRange": { "low": 24000, "high": 35000 },
  "airbagDeployment": true,
  "totalLossCandidate": true,
  "structuralDamage": true
}
```

```json
// ImageAnalyzer: Analyze damage photo 2 of 6 — interior and frame
{
  "tool": "ImageAnalyzer",
  "method": "analyzeDamage",
  "params": {
    "imageBase64": "<base64-encoded-photo-interior-frame-02>",
    "vehicleContext": {
      "year": 2021,
      "make": "Hyundai",
      "model": "Tucson"
    }
  }
}
```

**Response:**
```json
{
  "damageRegions": [
    {
      "part": "center_console",
      "damageType": "intrusion",
      "severity": "severe",
      "confidenceScore": 0.94,
      "boundingBox": { "x": 200, "y": 200, "w": 300, "h": 200 }
    },
    {
      "part": "structural_frame_right",
      "damageType": "deformed",
      "severity": "catastrophic",
      "confidenceScore": 0.96,
      "notes": "Unibody frame visibly bent. Vehicle is structurally compromised."
    },
    {
      "part": "side_airbags",
      "damageType": "deployed",
      "severity": "deployed",
      "confidenceScore": 0.99
    }
  ],
  "overallSeverity": "catastrophic",
  "totalLossCandidate": true,
  "structuralDamage": true
}
```

The ImageAnalyzer flags this as a **total loss candidate** — repair costs ($24,000–$35,000) exceed the vehicle's fair market value ($22,000).

#### Step 3 — Create the Claim Record

```json
// MongoDB MCP: insertOne into claims collection
{
  "tool": "mongodb_mcp",
  "method": "insertOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "document": {
      "claimId": "CLM-2025-00531",
      "policyNumber": "POL-2024-62718",
      "claimant": "Aisha Thompson",
      "dateOfLoss": "2025-06-10T14:30:00Z",
      "dateReported": "2025-06-10T16:00:00Z",
      "status": "filed",
      "type": "collision",
      "complexity": "high",
      "description": "T-bone collision at intersection. Other driver ran red light and struck claimant's vehicle on passenger side at approximately 40 mph. Passenger doors caved in, B-pillar bent, structural frame deformed, side airbags deployed. Vehicle towed, undrivable. Preliminary total loss assessment. Other driver cited for running red light. Two independent witnesses confirmed claimant had green light.",
      "location": {
        "intersection": "Oak Street & Riverside Boulevard",
        "city": "Denver",
        "state": "CO"
      },
      "policeReportNumber": "DPD-2025-14209",
      "otherParty": {
        "identified": true,
        "vehicle": "Dodge Ram pickup (red)",
        "citedForViolation": true,
        "violation": "running_red_light",
        "insuranceExchanged": true
      },
      "witnesses": [
        { "type": "independent", "statementProvided": true },
        { "type": "independent", "statementProvided": true }
      ],
      "injuries": {
        "reported": true,
        "claimantInjuries": [
          {
            "type": "seatbelt_bruising",
            "severity": "minor",
            "treatmentSought": "self_monitoring",
            "hospitalTransport": false
          }
        ]
      },
      "damages": [
        { "part": "passenger_front_door", "type": "caved_in", "severity": "catastrophic" },
        { "part": "passenger_rear_door", "type": "caved_in", "severity": "catastrophic" },
        { "part": "b_pillar", "type": "bent_structural", "severity": "catastrophic" },
        { "part": "rocker_panel_right", "type": "crushed", "severity": "severe" },
        { "part": "center_console", "type": "intrusion", "severity": "severe" },
        { "part": "structural_frame_right", "type": "deformed", "severity": "catastrophic" },
        { "part": "side_airbags", "type": "deployed", "severity": "deployed" }
      ],
      "airbagDeployment": true,
      "structuralDamage": true,
      "totalLossCandidate": true,
      "vehicleDrivable": false,
      "vehicleTowed": true,
      "estimatedRepairCost": null,
      "vehicleFairMarketValue": 22000,
      "deductible": 1000,
      "coverageApplied": "collision",
      "additionalCoverages": ["medicalPayments", "rentalReimbursement"],
      "imageAnalysisResults": [
        { "photoId": "img-040", "overallSeverity": "catastrophic", "confidence": 0.99, "totalLossCandidate": true },
        { "photoId": "img-041", "overallSeverity": "catastrophic", "confidence": 0.96, "totalLossCandidate": true }
      ],
      "flags": ["total_loss_candidate", "structural_damage", "airbag_deployment", "injuries_reported"],
      "createdAt": "2025-06-10T16:00:00Z",
      "updatedAt": "2025-06-10T16:00:00Z"
    }
  }
}
```

**Response:**
```json
{
  "acknowledged": true,
  "insertedId": "65f5e6f7a8b9c0d1e2f3a4b5"
}
```

#### Step 4 — Generate Claim Embedding

```json
// EmbeddingGenerator: Generate embedding for the claim description
{
  "tool": "EmbeddingGenerator",
  "method": "generateEmbedding",
  "params": {
    "model": "text-embedding-3-small",
    "input": "T-bone collision at intersection. Other driver ran red light, struck passenger side at 40 mph. Doors caved in, B-pillar bent, structural frame deformed, side airbags deployed. Vehicle totaled — repair cost exceeds fair market value of $22,000. Other driver cited, two witnesses confirm green light. Minor seatbelt bruising. Vehicle towed, undrivable.",
    "dimensions": 1536
  }
}
```

**Response:**
```json
{
  "embedding": [0.0567, -0.0890, 0.1123, "...1536 floats total..."],
  "model": "text-embedding-3-small",
  "tokensUsed": 68
}
```

```json
// MongoDB MCP: updateOne — store embedding on the claim document
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00531" },
    "update": {
      "$set": {
        "embedding": [0.0567, -0.0890, 0.1123, "...1536 floats..."],
        "status": "pending_assessment",
        "updatedAt": "2025-06-10T16:01:00Z"
      }
    }
  }
}
```

---

### What the Assessment Agent Determines

#### Step 1 — Retrieve the Filed Claim

```json
// MongoDB MCP: findOne on claims collection
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00531" }
  }
}
```

#### Step 2 — Search for Similar Historical Claims

```json
// MongoDB MCP: aggregate — $vectorSearch for similar total loss claims
{
  "tool": "mongodb_mcp",
  "method": "aggregate",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "pipeline": [
      {
        "$vectorSearch": {
          "index": "claims_vector_index",
          "path": "embedding",
          "queryVector": [0.0567, -0.0890, 0.1123, "...1536 floats..."],
          "numCandidates": 150,
          "limit": 5,
          "filter": {
            "status": "closed",
            "totalLossCandidate": true
          }
        }
      },
      {
        "$project": {
          "claimId": 1,
          "description": 1,
          "vehicleFairMarketValue": 1,
          "totalLossPayout": 1,
          "resolution": 1,
          "score": { "$meta": "vectorSearchScore" }
        }
      }
    ]
  }
}
```

**Response:**
```json
[
  {
    "claimId": "CLM-2024-40112",
    "description": "T-bone at intersection. Other party ran stop sign. Passenger side destroyed, structural damage. Total loss.",
    "vehicleFairMarketValue": 24500,
    "totalLossPayout": 23500,
    "resolution": "total_loss_approved",
    "score": 0.94
  },
  {
    "claimId": "CLM-2024-38790",
    "description": "Side impact collision at intersection. Structural frame bent, airbags deployed. Vehicle totaled.",
    "vehicleFairMarketValue": 19800,
    "totalLossPayout": 18800,
    "resolution": "total_loss_approved",
    "score": 0.92
  },
  {
    "claimId": "CLM-2024-42501",
    "description": "Red light violation caused T-bone. Complete passenger side destruction. Total loss declared.",
    "vehicleFairMarketValue": 26000,
    "totalLossPayout": 25000,
    "resolution": "total_loss_approved",
    "score": 0.90
  }
]
```

#### Step 3 — Vehicle Valuation Lookup

The Assessment Agent cross-references the vehicle's fair market value using multiple sources.

```json
// MongoDB MCP: findOne — vehicle valuation database
{
  "tool": "mongodb_mcp",
  "method": "findOne",
  "params": {
    "database": "insurance",
    "collection": "vehicle_valuations",
    "filter": {
      "vin": "5NMJF3AE0MH456789"
    }
  }
}
```

**Response:**
```json
{
  "vin": "5NMJF3AE0MH456789",
  "year": 2021,
  "make": "Hyundai",
  "model": "Tucson",
  "trim": "SEL",
  "mileage": 38500,
  "condition": "good",
  "valuationSources": {
    "kbb": 21800,
    "nada": 22200,
    "edmunds": 21600
  },
  "averageFairMarketValue": 21867,
  "adjustedValue": 22000,
  "valuationDate": "2025-06-10"
}
```

Average fair market value: **$22,000**. This confirms the declared value.

#### Step 4 — Total Loss Determination & Payout Calculation

The Assessment Agent confirms total loss: estimated repair ($24,000–$35,000) exceeds the vehicle's fair market value ($22,000). Under total loss rules, the payout is the vehicle's fair market value minus the deductible.

```json
// MongoDB MCP: updateOne — record total loss assessment
{
  "tool": "mongodb_mcp",
  "method": "updateOne",
  "params": {
    "database": "insurance",
    "collection": "claims",
    "filter": { "claimId": "CLM-2025-00531" },
    "update": {
      "$set": {
        "status": "approved_total_loss",
        "assessment": {
          "decision": "total_loss_approved",
          "assessedAt": "2025-06-10T17:45:00Z",
          "totalLossDeclared": true,
          "vehicleFairMarketValue": 22000,
          "valuationMethod": "average_of_kbb_nada_edmunds",
          "deductibleApplied": 1000,
          "payoutAmount": 21000,
          "salvageValue": 3200,
          "salvageRetained": false,
          "coverageUsed": "collision",
          "liabilityDetermination": "other_party_at_fault",
          "fraudRiskScore": 0.01,
          "similarClaimsReferenced": ["CLM-2024-40112", "CLM-2024-38790", "CLM-2024-42501"],
          "reasoning": "Total loss confirmed — estimated repair cost ($24,000–$35,000) exceeds fair market value ($22,000) by significant margin. Structural frame damage and B-pillar deformation make repair economically unviable and potentially unsafe. Liability is clear: other driver cited for running red light, corroborated by two independent witnesses and police report. Payout calculated as FMV ($22,000) minus deductible ($1,000) = $21,000. Salvage value estimated at $3,200. No fraud indicators.",
          "requiresManualReview": false,
          "rentalCoverage": {
            "approved": true,
            "dailyRate": 45,
            "maxDays": 30,
            "estimatedRentalDays": 14,
            "note": "Rental authorized until settlement check is issued or replacement vehicle is obtained, whichever comes first, up to 30 days."
          },
          "medicalPayments": {
            "note": "Claimant reports minor seatbelt bruising, no treatment sought. MedPay coverage ($5,000 limit) available if claimant seeks treatment.",
            "reserved": 1000
          },
          "subrogation": {
            "eligible": true,
            "targetInsurer": "Other party's carrier",
            "expectedRecovery": "Full payout + deductible",
            "note": "Other driver 100% at fault (cited, witness-corroborated). Full subrogation recovery expected, including claimant's deductible."
          },
          "nextSteps": [
            "Issue total loss settlement offer of $21,000 to claimant",
            "Obtain title from claimant for salvage transfer",
            "Activate rental reimbursement (up to $45/day, 30 days)",
            "Initiate subrogation against other party's insurer",
            "Monitor for medical payment claims"
          ]
        },
        "updatedAt": "2025-06-10T17:45:00Z"
      }
    }
  }
}
```

**Response:**
```json
{ "acknowledged": true, "matchedCount": 1, "modifiedCount": 1 }
```

**Outcome:** Vehicle declared a **total loss**. Aisha Thompson receives **$21,000** ($22,000 fair market value − $1,000 deductible). She is approved for **rental car reimbursement** at $45/day for up to 30 days. The insurer will pursue **full subrogation** against the other driver's carrier, including recovery of Aisha's $1,000 deductible. MedPay coverage ($5,000) remains available if she seeks treatment for her bruising.

---

## Summary Table

| # | Scenario | Customer | Claim ID | Damage | Decision | Payout |
|---|----------|----------|----------|--------|----------|--------|
| 1 | Rear-End at Stoplight | Sarah Chen | CLM-2025-00143 | Minor | ✅ Approved | $2,300 |
| 2 | Parking Lot Hit-and-Run | Marcus Williams | CLM-2025-00287 | Moderate | ✅ Approved | $5,950 |
| 3 | Multi-Vehicle Highway | Jennifer Park | CLM-2025-00412 | Severe | ⏳ Under Investigation | ~$17,500* |
| 4 | Weather — Ice/Guardrail | David Kowalski | CLM-2025-00098 | Moderate | ✅ Approved | $3,600 |
| 5 | Total Loss T-Bone | Aisha Thompson | CLM-2025-00531 | Catastrophic | ✅ Total Loss | $21,000 |

\* *Pending liability investigation and manual review.*
