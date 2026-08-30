# Circle group bounds

Fix grouped BioScan circle payloads so their radius contributes to Fill-mode
group bounds. The current grouping path records only the circle centre, while
the renderer draws the full diameter. That geometry mismatch causes the group
to jump when payloads refresh.
