from qgis.core import QgsTask, QgsMessageLog, Qgis
from .valhalla_client import ValhallaError


class RouteTask(QgsTask):
    def __init__(self, description, client, waypoints, costing="auto",
                 costing_options=None, directions_options=None, optimized=False,
                 date_time=None):
        super().__init__(description, QgsTask.Flag.CanCancel)
        self.client = client
        self.waypoints = waypoints
        self.costing = costing
        self.costing_options = costing_options
        self.directions_options = directions_options
        self.optimized = optimized
        self.date_time = date_time
        self.response = None
        self.error = None
        self.result_ok = False

    def run(self):
        if self.isCanceled():
            return False
        try:
            if self.optimized:
                self.response = self.client.optimized_route(
                    self.waypoints, self.costing,
                    self.costing_options, self.directions_options,
                    date_time=self.date_time,
                )
            else:
                self.response = self.client.route(
                    self.waypoints, self.costing,
                    self.costing_options, self.directions_options,
                    date_time=self.date_time,
                )
            if self.isCanceled():
                return False
            self.result_ok = True
            return True
        except ValhallaError as e:
            self.error = e
            return False
        except Exception as e:
            self.error = ValhallaError("invalid", -1, str(e))
            return False

    def finished(self, result):
        if not result and self.error:
            QgsMessageLog.logMessage(
                f"RouteTask failed: {self.error.message}", "Routing Plan", Qgis.Warning
            )

    def cancel(self):
        QgsMessageLog.logMessage("Route computation cancelled by user", "Routing Plan", Qgis.Info)
        super().cancel()
