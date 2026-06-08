# WHO recommended adult vaccination schedule
# interval_years: how often this vaccine is needed (None = one-time)
# doses: total doses in the series

WHO_ADULT_SCHEDULE = {
"Influenza": {
"interval_years": 1,
"doses": 1,
"notes": "Annual flu shot recommended for all adults"
},
"Td": {
"interval_years": 10,
"doses": 1,
"notes": "Tetanus-diphtheria booster every 10 years"
},
"Tdap": {
"interval_years": None,
"doses": 1,
"notes": "One-time Tdap booster if not received as adult"
},
"Hepatitis B": {
"interval_years": None,
"doses": 3,
"notes": "3-dose series if not vaccinated"
},
"Hepatitis A": {
"interval_years": None,
"doses": 2,
"notes": "2-dose series if not vaccinated"
},
"MMR": {
"interval_years": None,
"doses": 2,
"notes": "2 doses if born after 1957 and not vaccinated"
},
"Varicella": {
"interval_years": None,
"doses": 2,
"notes": "2 doses if no history of chickenpox"
},
"Pneumococcal": {
"interval_years": None,
"doses": 1,
"notes": "Recommended for adults 65+ or high-risk groups"
},
"COVID-19": {
"interval_years": 1,
"doses": 1,
"notes": "Annual updated booster recommended"
},
"Typhoid": {
"interval_years": 3,
"doses": 1,
"notes": "Every 3 years for those in endemic areas"
},
}