// ==============================================================================
// CIT 21MDS56: Air Quality & Public Health Early-Warning System
// mongo/aggregations.js - Unstructured Complaint Text Analytics & Aggregation
// ==============================================================================

db = db.getSiblingDB("air_quality_ews");

// Aggregation Pipeline for Daily Zone Complaint & Symptom Keyword Frequency
const complaintAggregationPipeline = [
  // 1. Unwind symptoms array to analyze individual keyword frequencies
  {
    $unwind: {
      path: "$symptoms",
      preserveNullAndEmptyArrays: true
    }
  },
  // 2. Normalize and classify symptom keywords
  {
    $project: {
      city: 1,
      zone_id: 1,
      zone_name: 1,
      date_str: 1,
      severity: 1,
      symptom: { $toLower: { $ifNull: ["$symptoms", "other"] } }
    }
  },
  // 3. Group by zone and day to aggregate counts and keyword occurrences
  {
    $group: {
      _id: {
        city: "$city",
        zone_id: "$zone_id",
        zone_name: "$zone_name",
        date: "$date_str"
      },
      total_symptom_mentions: { $sum: 1 },
      avg_reported_severity: { $avg: "$severity" },
      breathing_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /breath|shortness|asthma|wheez/i } }, 1, 0]
        }
      },
      chest_pain_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /chest/i } }, 1, 0]
        }
      },
      eye_irritation_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /eye|burn/i } }, 1, 0]
        }
      },
      cough_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /cough|throat/i } }, 1, 0]
        }
      },
      headache_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /headache|nausea/i } }, 1, 0]
        }
      },
      smog_count: {
        $sum: {
          $cond: [{ $regexMatch: { input: "$symptom", regex: /smog|haze/i } }, 1, 0]
        }
      }
    }
  },
  // 4. Calculate weighted composite symptom severity index (0.0 - 1.0)
  {
    $project: {
      _id: 0,
      city: "$_id.city",
      zone_id: "$_id.zone_id",
      zone_name: "$_id.zone_name",
      date: "$_id.date",
      total_mentions: "$total_symptom_mentions",
      avg_severity: { $round: ["$avg_reported_severity", 2] },
      symptom_severity_score: {
        $round: [
          {
            $min: [
              1.0,
              {
                $divide: [
                  {
                    $add: [
                      { $multiply: ["$breathing_count", 1.0] },
                      { $multiply: ["$chest_pain_count", 0.9] },
                      { $multiply: ["$eye_irritation_count", 0.6] },
                      { $multiply: ["$cough_count", 0.5] },
                      { $multiply: ["$headache_count", 0.4] },
                      { $multiply: ["$smog_count", 0.3] }
                    ]
                  },
                  { $max: [1.0, { $multiply: ["$total_symptom_mentions", 0.8] }] }
                ]
              }
            ]
          },
          3
        ]
      },
      keywords: {
        breathing: "$breathing_count",
        chest_pain: "$chest_pain_count",
        eye_irritation: "$eye_irritation_count",
        cough: "$cough_count",
        headache: "$headache_count",
        smog: "$smog_count"
      }
    }
  },
  {
    $sort: { date: -1, city: 1, zone_id: 1 }
  }
];

// Sample execution print
printjson(db.symptom_reports.aggregate(complaintAggregationPipeline).toArray().slice(0, 5));
