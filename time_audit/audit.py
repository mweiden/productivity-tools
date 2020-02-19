import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tzlocal import get_localzone
from dateutil.parser import parse as dt_parse


class TimeAudit:
    def __init__(self, events, creative_hours_start_date, subplots=False):
        self.creative_hours_start_date = creative_hours_start_date
        self.labels = sorted(list(set(e.label for e in events)))
        num_labels = len(self.labels)
        self.label_to_ind = dict(zip(self.labels, range(num_labels)))

        split_events = []
        for event in events:
            split_events.extend(event.split_by_date())
        self.events = sorted(split_events, key=lambda x: x.start_datetime)

        # date buckets
        dates = set()
        for event in split_events:
            dates.add(
                event.start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            )
        self.dates = sorted(list(dates))
        self.num_days = len(self.dates)
        self.date_to_ind = dict(zip(self.dates, range(self.num_days)))

        # generate matrix of event times
        self.time_mat = np.zeros((num_labels, self.num_days))

        for event in split_events:
            date_ind = self.date_to_ind[
                event.start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            ]
            label_ind = self.label_to_ind[event.label]
            self.time_mat[label_ind, date_ind] += (
                    event.duration().total_seconds() / 3600
            )

        # Reading
        self.reading_pages = np.zeros(self.num_days)

        for event in split_events:
            if not ('Reading' in event.label and 'Pages' in event.description_attributes):
                continue
            date_ind = self.date_to_ind[
                event.start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            ]
            self.reading_pages[date_ind] += int(event.description_attributes['Pages'])

        # context switches
        self.context_switches = np.zeros(self.num_days)

        for event in split_events:
            date_ind = self.date_to_ind[
                event.start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            ]
            self.context_switches[date_ind] += 1

        self.context_switches -= 1.0
        self.context_switches[self.context_switches < 0] = 0.0

        # cumulative creative time
        self.creative_hours = np.zeros(self.num_days)
        for label in ["Reading", "Meta", "Audiobook", "Studying", "Programming", "Networking"]:
            if label in self.label_to_ind:
                ind = self.label_to_ind[label]
                self.creative_hours += self.time_mat[ind, :]
        self.cumulative_creative_hours = np.cumsum(self.creative_hours)

        start_date = dt_parse("2019-12-21").astimezone(get_localzone())
        self.creative_hours_goal = []
        for date in self.dates:
            days_since_start = max((date - start_date).days, 0)
            self.creative_hours_goal.append(1000.0 / 365.0 * days_since_start)

    def plots(self, renderer=None):
        # days in the moving average
        ma_days = 7

        def moving_average(data_set, periods=3):
            weights = np.ones(periods) / periods
            return np.convolve(data_set, weights, mode="valid")

        fig = make_subplots(
            rows=3,
            cols=2,
            specs=[[{}, {}], [{"colspan": 2}, None], [{}, {}]],
            subplot_titles=(
                f"Time Audit (moving average, {ma_days} days)",
                "Context Switches",
                "Averages (First Half, Second Half)",
                "Reading (Pages)",
                "Creative Hours",
            ),
        )

        # plot usage over time (100% area plot)
        current_row = 1
        current_col = 1

        percent = np.zeros((len(self.labels), self.num_days - ma_days + 1))

        for row_i in range(percent.shape[0]):
            percent[row_i, :] = moving_average(self.time_mat[row_i, :], ma_days)

        norm = percent.sum(axis=0).astype(float)
        norm[norm == 0.0] = 1
        percent = percent / norm * 100.0

        for label, day_percent in sorted(zip(self.labels, percent), key=lambda x: x[1][-1]):
            fig.add_trace(
                go.Scatter(
                    name=label,
                    x=self.dates[ma_days - 1:],
                    y=day_percent,
                    hoverinfo="name+x+y",
                    mode="lines",
                    stackgroup="one",  # define stack group
                ),
                row=current_row,
                col=current_col,
            )
        fig.update_yaxes(range=(0, 100), row=current_row, col=current_col)

        # context switches
        current_row = 1
        current_col = 2
        fig.add_trace(
            go.Bar(
                x=self.dates,
                y=self.context_switches,
                name="context switches",
                marker_color="royalblue",
            ),
            row=current_row,
            col=current_col,
        )
        fig.add_trace(
            go.Scatter(
                x=self.dates[ma_days - 1:],
                y=moving_average(self.context_switches, ma_days),
                mode="lines",
                marker_color="rgb(0, 255, 0)",
            ),
            row=current_row,
            col=current_col,
        )
        fig.update_yaxes(rangemode="tozero", row=current_row, col=current_col)

        # Averages
        current_row = 2
        current_col = 1
        first_half_averages = np.mean(
            self.time_mat[:, : int(self.num_days / 2)],
            axis=1
        ) / 24.0
        second_half_averages = np.mean(
            self.time_mat[:, int(self.num_days / 2): -1],
            axis=1
        ) / 24.0
        tmp = sorted(zip(self.labels, first_half_averages, second_half_averages), key=lambda x: x[2])
        avg_labels = [x[0] for x in tmp]
        first_half_averages = [x[1] for x in tmp]
        second_half_averages = [x[2] for x in tmp]
        fig.add_trace(
            go.Bar(
                x=avg_labels,
                y=first_half_averages,
                marker_color="rgb(55, 83, 109)",
                name="First Half",
            ),
            row=current_row,
            col=current_col,
        )

        fig.add_trace(
            go.Bar(
                x=avg_labels,
                y=second_half_averages,
                marker_color="rgb(26, 118, 255)",
                name="Second Half",
            ),
            row=current_row,
            col=current_col,
        )

        # Reading
        current_row = 3
        current_col = 1
        fig.add_trace(
            go.Scatter(
                x=self.dates,
                y=np.cumsum(self.reading_pages),
                mode="lines",
                name="Pages",
                line=dict(color="royalblue"),
            ),
            row=current_row,
            col=current_col,
        )
        fig.add_trace(
            go.Scatter(
                x=self.dates,
                y=np.cumsum(np.ones(self.num_days) * 20),
                mode="lines",
                name="goal",
                line=dict(dash="dash", color="red"),
            ),
            row=current_row,
            col=current_col,
        )
        fig.update_yaxes(rangemode="tozero", row=current_row, col=current_col)

        # plot creative hours over time (line plot)
        current_row = 3
        current_col = 2
        fig.add_trace(
            go.Scatter(
                x=self.dates,
                y=self.cumulative_creative_hours,
                mode="lines",
                name="creative hours",
                line=dict(color="royalblue"),
            ),
            row=current_row,
            col=current_col,
        )
        fig.add_trace(
            go.Scatter(
                x=self.dates,
                y=self.creative_hours_goal,
                mode="lines",
                name="goal",
                line=dict(dash="dash", color="red"),
            ),
            row=current_row,
            col=current_col,
        )
        fig.update_yaxes(rangemode="tozero", row=current_row, col=current_col)

        fig.show(renderer=renderer)
