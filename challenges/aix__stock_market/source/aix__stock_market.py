from sklearn.metrics import log_loss


def official_evaluation_metric(target, predictions):
    return {'log_loss': log_loss(target, predictions)}
