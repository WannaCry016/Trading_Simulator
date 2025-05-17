#pragma once

#include <QMainWindow>
#include <QString>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onRunSimulationClicked();

private:
    Ui::MainWindow *ui;

    void updateOutput(double slippage, double fee, double impact, double netCost, double makerProb, double takerProb);
};
