{{- define "leaflet.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "leaflet.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "leaflet.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "leaflet.labels" -}}
helm.sh/chart: {{ include "leaflet.chart" . }}
app.kubernetes.io/name: {{ include "leaflet.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: leaflet
{{- end }}

{{- define "leaflet.selectorLabels" -}}
app.kubernetes.io/name: {{ include "leaflet.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "leaflet.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "leaflet.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "leaflet.secretName" -}}
{{- if .Values.envSecret.name }}
{{- .Values.envSecret.name }}
{{- else }}
{{- printf "%s-env" (include "leaflet.fullname" .) }}
{{- end }}
{{- end }}

{{- define "leaflet.apiImage" -}}
{{- printf "%s:%s" .Values.api.image.repository .Values.api.image.tag }}
{{- end }}

{{- define "leaflet.webImage" -}}
{{- printf "%s:%s" .Values.web.image.repository .Values.web.image.tag }}
{{- end }}
