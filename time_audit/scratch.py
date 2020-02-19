while ind_transitions < (len(transitions) - 1):
    print(
        f"day_bucket[{ind_day_buckets}]={day_buckets[ind_day_buckets]}, transitions[{ind_transitions}]={transitions[ind_transitions][0].isoformat()}"
    )

    if transitions[ind_transitions + 1][0] < day_buckets[ind_day_buckets + 1]:
        print("advance transitions")
        ind_transitions += 1
    else:
        print("advance day bucket")
        ind_day_buckets += 1

active_set = set()
for dt, changes in sorted(transitions.items(), key=lambda x: x[0]):
    added = set()
    removed = set()

    for summary, delta in changes.items():
        if delta > 0:
            added.add(summary)
        elif delta < 0:
            removed.add(summary)

    did_not_change = active_set - removed
    active_set |= added
    active_set -= removed

    date_ind = date_to_ind[dt.replace(hour=0, minute=0, second=0, microsecond=0)]

    for summary in added:
        summary_ind = summary_to_ind[summary]
