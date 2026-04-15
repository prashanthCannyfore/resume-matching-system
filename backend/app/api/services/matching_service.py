from app.api.services.filter_service import filter_candidates


def get_filtered_candidates(candidates, job):
    return filter_candidates(candidates, job)